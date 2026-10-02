from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, Client
from django.utils import timezone

from login.disappearing import create_message, conversation_messages, timer_for, update_timer
from login.models import ConversationTimer
from login.otp import issue_challenge, verify_challenge, CHALLENGE_KEY, clear_pending
from register.models import Message, Register


class DisappearingMessageTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.alex = Register.objects.create(first_name='Alex', email='alex@example.com', date=now.date(), time=now)
        self.jo = Register.objects.create(first_name='Jo', email='jo@example.com', date=now.date(), time=now)
        self.url = f'/login/chat/{self.jo.pk}/'
        session = self.client.session
        session.update({'u_id':self.alex.pk, 'type':'user'})
        session.save()
        self.follows = patch('register.models.Follower.objects.filter')
        self.follows.start().return_value.exists.return_value = True
        self.addCleanup(self.follows.stop)

    def test_setting_is_shared_and_survives_reload(self):
        result = self.client.post(self.url+'timer/', {'duration':86400,'revision':0})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(timer_for(self.jo.pk, self.alex.pk).duration, 86400)
        self.assertContains(self.client.get(self.url), '24 hours')
        self.assertEqual(ConversationTimer.objects.count(), 1)

    def test_stale_setting_cannot_overwrite_other_person(self):
        self.client.post(self.url+'timer/', {'duration':86400,'revision':0})
        result = self.client.post(self.url+'timer/', {'duration':0,'revision':0})
        self.assertEqual(result.status_code, 409)
        self.assertEqual(timer_for(self.alex.pk,self.jo.pk).duration, 86400)

    def test_invalid_durations_rejected(self):
        for duration in ('-1','abc','1','999999999'):
            self.assertEqual(self.client.post(self.url+'timer/', {'duration':duration,'revision':0}).status_code,400)
        self.assertFalse(ConversationTimer.objects.exists())

    def test_csrf_required_for_setting(self):
        strict = Client(enforce_csrf_checks=True)
        strict.cookies = self.client.cookies
        self.assertEqual(strict.post(self.url+'timer/',{'duration':60,'revision':0}).status_code,403)

    def test_unauthorized_and_revoked_relationships(self):
        self.assertEqual(Client().get(self.url+'state/').status_code,401)
        with patch('login.views.can_chat',return_value=False):
            self.assertEqual(self.client.get(self.url+'state/').status_code,403)
            self.assertEqual(self.client.post(self.url+'timer/', {'duration':60,'revision':0}).status_code,403)
        self.assertFalse(ConversationTimer.objects.exists())

    def test_server_uses_saved_duration_not_posted_flag(self):
        self.client.post(self.url+'timer/',{'duration':60,'revision':0})
        before = timezone.now()
        result = self.client.post(self.url,{'content':'Hello there','is_disappearing':'false','expire_timeline':'1y'})
        self.assertEqual(result.status_code,302)
        message = Message.objects.get()
        self.assertEqual(message.disappearing_seconds,60)
        self.assertGreaterEqual(message.expires_at,before+timedelta(seconds=60))

    def test_off_only_changes_future_messages(self):
        original = create_message(self.alex.pk,self.jo.pk,'Timed',60)
        self.client.post(self.url+'timer/',{'duration':60,'revision':0})
        self.client.post(self.url+'timer/',{'duration':0,'revision':1})
        self.client.post(self.url,{'content':'This one stays'})
        original.refresh_from_db()
        self.assertIsNotNone(original.expires_at)
        permanent = Message.objects.exclude(pk=original.pk).get()
        self.assertFalse(permanent.is_disappearing)
        self.assertIsNone(permanent.expires_at)

    def test_viewing_does_not_delete_unexpired_message(self):
        message = create_message(self.jo.pk,self.alex.pk,'Still here',60)
        self.assertContains(self.client.get(self.url),'Still here')
        self.assertContains(self.client.get(self.url),'Still here')
        self.assertTrue(Message.objects.filter(pk=message.pk).exists())

    def test_expiry_boundary_hides_and_deletes_for_both_people(self):
        message = create_message(self.alex.pk,self.jo.pk,'Private text',60)
        cutoff = message.expires_at
        self.assertEqual(conversation_messages(self.jo.pk,self.alex.pk,cutoff-timedelta(microseconds=1)).count(),1)
        self.assertEqual(conversation_messages(self.alex.pk,self.jo.pk,cutoff).count(),0)
        self.assertFalse(Message.objects.filter(pk=message.pk).exists())

    def test_poll_never_returns_expired_content_and_is_not_cached(self):
        message = create_message(self.jo.pk,self.alex.pk,'Expired private text',60)
        Message.objects.filter(pk=message.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        response = self.client.get(self.url+'state/')
        self.assertNotIn('Expired private text',response.json()['html'])
        self.assertIn('no-store',response['Cache-Control'])
        self.assertFalse(Message.objects.exists())

    def test_purge_removes_only_expired_messages(self):
        expired = create_message(self.alex.pk,self.jo.pk,'Old',60)
        Message.objects.filter(pk=expired.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        active = create_message(self.alex.pk,self.jo.pk,'Active',60)
        permanent = create_message(self.alex.pk,self.jo.pk,'Kept',0)
        call_command('purge_expired_messages',stdout=StringIO())
        self.assertSetEqual(set(Message.objects.values_list('pk',flat=True)),{active.pk,permanent.pk})

    def test_read_endpoint_requires_recipient_and_post(self):
        message = create_message(self.alex.pk,self.jo.pk,'Text',60)
        url = f'/login/read_disappearing/{message.pk}/'
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url).status_code,404)
        message.refresh_from_db()
        self.assertEqual(message.is_read,0)

    def test_message_html_is_escaped(self):
        create_message(self.jo.pk,self.alex.pk,'<img src=x onerror=alert(1)>',60)
        html = self.client.get(self.url+'state/').json()['html']
        self.assertIn('&lt;img',html)
        self.assertNotIn('<img src=x',html)

    def test_financial_otp_binds_duration_and_starts_expiry_after_verification(self):
        session = {'pending_financial_receiver':self.jo.pk,'pending_financial_msg':'money',
                   'pending_is_disappearing':True,'pending_disappearing_seconds':60}
        with patch('login.otp.secrets.randbelow',return_value=123789):
            self.assertTrue(issue_challenge(session,self.alex)[0])
        session['pending_disappearing_seconds'] = 86400
        self.assertFalse(verify_challenge(session,self.alex,'123789')[0])
        clear_pending(session)
        self.assertNotIn('pending_disappearing_seconds',session)

    def test_financial_message_keeps_timer_through_otp(self):
        self.client.post(self.url+'timer/',{'duration':60,'revision':0})
        with patch('login.otp.secrets.randbelow',return_value=123789):
            self.assertRedirects(self.client.post(self.url,{'content':'send money'}),'/login/financial_otp_verify/',fetch_redirect_response=False)
        self.assertFalse(Message.objects.exists())
        self.client.post(self.url+'timer/',{'duration':0,'revision':1})
        before = timezone.now()
        self.client.post('/login/financial_otp_verify/',{'otp':'123789'})
        message = Message.objects.get()
        self.assertEqual(message.disappearing_seconds,60)
        self.assertGreaterEqual(message.expires_at,before+timedelta(seconds=60))
        self.client.post('/login/financial_otp_verify/',{'otp':'123789'})
        self.assertEqual(Message.objects.count(),1)
