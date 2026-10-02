from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.core import mail
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import SimpleTestCase, RequestFactory, override_settings
from login.otp import CHALLENGE_KEY, challenge_state, clear_pending, issue_challenge, verify_challenge


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='AssentTag <sender@example.com>')
class EmailOTPTests(SimpleTestCase):
    def setUp(self):
        self.user = SimpleNamespace(register_id=12, email='recipient@example.com', first_name='<Alex>')
        self.session = SessionStore()
        self.session.update({'u_id': 12, 'type': 'user', 'pending_financial_msg': 'Please send money', 'pending_financial_receiver': 14, 'pending_is_disappearing': True})

    def issue(self, code=234567):
        with patch('login.otp.secrets.randbelow', return_value=code):
            sent, notice = issue_challenge(self.session, self.user)
        self.assertTrue(sent, notice)

    def test_mail_delivery_and_single_use(self):
        self.issue()
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('234567', mail.outbox[0].body)
        self.assertIn('&lt;Alex&gt;', mail.outbox[0].alternatives[0][0])
        self.assertNotIn('234567', str(dict(self.session)))
        self.assertTrue(verify_challenge(self.session, self.user, '234567')[0])
        self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])

    def test_leading_zero_code(self):
        self.issue(42)
        self.assertTrue(verify_challenge(self.session, self.user, '000042')[0])

    def test_expiry(self):
        with patch('login.otp.time.time', return_value=10000): self.issue()
        with patch('login.otp.time.time', return_value=10300):
            self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])
        self.assertNotIn(CHALLENGE_KEY, self.session)

    def test_attempt_lockout(self):
        self.issue()
        for _ in range(5): self.assertFalse(verify_challenge(self.session, self.user, '123456')[0])
        self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])

    def test_countdown_state_clears_expired_code(self):
        with patch('login.otp.time.time', return_value=10000): self.issue()
        with patch('login.otp.time.time', return_value=10030):
            state = challenge_state(self.session, self.user)
            self.assertEqual(state['otp_remaining_seconds'], 270)
            self.assertEqual(state['resend_remaining_seconds'], 30)
            self.assertTrue(state['code_sent'])
            self.assertNotIn('digest', state)
        with patch('login.otp.time.time', return_value=10300):
            state = challenge_state(self.session, self.user)
            self.assertTrue(state['code_expired'])
            self.assertFalse(state['code_sent'])
            self.assertEqual(state['resend_remaining_seconds'], 0)
        self.assertNotIn(CHALLENGE_KEY, self.session)

    def test_resend_after_timeout_accepts_only_replacement(self):
        with patch('login.otp.time.time', return_value=10000): self.issue()
        with patch('login.otp.time.time', return_value=10301):
            self.assertTrue(challenge_state(self.session, self.user)['code_expired'])
            self.issue(345678)
            self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])
            self.assertTrue(verify_challenge(self.session, self.user, '345678')[0])

    def test_countdown_state_rejects_changed_message(self):
        self.issue()
        self.session['pending_financial_msg'] = 'different message'
        self.assertFalse(challenge_state(self.session, self.user)['code_sent'])
        self.assertNotIn(CHALLENGE_KEY, self.session)

    def test_message_binding(self):
        self.issue()
        self.session['pending_financial_receiver'] = 99
        self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])

    def test_email_binding(self):
        self.issue()
        self.user.email = 'changed@example.com'
        self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])

    def test_resend_cooldown_and_invalidation(self):
        with patch('login.otp.time.time', return_value=10000):
            self.issue()
            self.assertFalse(issue_challenge(self.session, self.user)[0])
        with patch('login.otp.time.time', return_value=10061): self.issue(345678)
        with patch('login.otp.time.time', return_value=10062):
            self.assertFalse(verify_challenge(self.session, self.user, '234567')[0])
            self.assertTrue(verify_challenge(self.session, self.user, '345678')[0])

    def test_hourly_limit(self):
        with patch('login.otp.time.time', return_value=10000): self.issue()
        for i in range(1, 5):
            with patch('login.otp.time.time', return_value=10000 + i * 61): self.issue()
        with patch('login.otp.time.time', return_value=10305): self.assertFalse(issue_challenge(self.session, self.user)[0])

    def test_delivery_failure_never_creates_token(self):
        with patch('login.otp.EmailMultiAlternatives.send', side_effect=OSError('offline')):
            self.assertFalse(issue_challenge(self.session, self.user)[0])
        self.assertNotIn(CHALLENGE_KEY, self.session)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='')
    def test_missing_credentials(self):
        self.assertFalse(issue_challenge(self.session, self.user)[0])
        self.assertNotIn(CHALLENGE_KEY, self.session)
        self.assertNotIn('financial_email_rate', self.session)

    def test_slow_delivery_gives_full_five_minutes(self):
        with patch('login.otp.time.time', side_effect=[10000, 10014]), patch('login.otp.EmailMultiAlternatives.send', return_value=1):
            self.issue()
        self.assertEqual(self.session[CHALLENGE_KEY]['expires'], 10314)
        with patch('login.otp.time.time', return_value=10014):
            state = challenge_state(self.session, self.user)
        self.assertEqual(state['otp_remaining_seconds'], 300)
        self.assertEqual(state['resend_remaining_seconds'], 60)

    def test_cancel_clears_pending_message(self):
        self.issue()
        clear_pending(self.session)
        self.assertNotIn(CHALLENGE_KEY, self.session)
        self.assertNotIn('pending_financial_msg', self.session)

    def test_view_sends_message_once_after_verification(self):
        from login.views import financial_otp_verify
        self.issue()
        request = RequestFactory().post('/login/financial_otp_verify/', {'otp': '234567'})
        request.session = self.session
        request._messages = FallbackStorage(request)
        with patch('login.views.Register.objects.filter') as users, patch('login.views.Follower.objects.filter') as follows, patch('login.views.Message.objects.create') as create:
            users.return_value.first.return_value = self.user
            follows.return_value.exists.return_value = True
            response = financial_otp_verify(request)
            self.assertEqual(response.status_code, 302)
            create.assert_called_once_with(sender_id=12, receiver_id=14, content='Please send money', is_disappearing=True)
            financial_otp_verify(request)
            self.assertEqual(create.call_count, 1)

    def test_revoked_follow_prevents_authorization(self):
        from login.views import financial_otp_verify
        self.issue()
        request = RequestFactory().post('/login/financial_otp_verify/', {'otp': '234567'})
        request.session = self.session
        with patch('login.views.Register.objects.filter') as users, patch('login.views.Follower.objects.filter') as follows, patch('login.views.Message.objects.create') as create:
            users.return_value.first.return_value = self.user
            follows.return_value.exists.return_value = False
            self.assertEqual(financial_otp_verify(request).status_code, 302)
            create.assert_not_called()
            self.assertNotIn(CHALLENGE_KEY, self.session)

    def test_user_login_redirects_to_dashboard(self):
        from login.views import add_login
        request = RequestFactory().post('/login/login/', {'email':'test@example.com', 'password':'test', 'role':'user'})
        request.session = self.session
        request._messages = FallbackStorage(request)
        account = SimpleNamespace(type='user', u_id=12)
        with patch('login.views.Login.objects.filter', return_value=[account]), patch('login.views.Register.objects.filter') as users:
            self.user.status = 'approved'
            users.return_value.first.return_value = self.user
            response = add_login(request)
        self.assertEqual(response.url, '/index/index3/')
        self.assertEqual(request.session['type'], 'user')
        self.assertTrue(any('login' in message.tags for message in request._messages))

    def test_admin_login_redirects_to_dashboard(self):
        from login.views import add_login
        request = RequestFactory().post('/login/login/', {'email':'test@example.com', 'password':'test', 'role':'admin'})
        request.session = self.session
        request._messages = FallbackStorage(request)
        with patch('login.views.Login.objects.filter', return_value=[SimpleNamespace(type='admin', u_id=1)]):
            response = add_login(request)
        self.assertEqual(response.url, '/index/index2/')
        self.assertEqual(request.session['type'], 'admin')
        self.assertTrue(any('admin-login' in message.tags for message in request._messages))

    def test_failed_login_does_not_show_success(self):
        from login.views import add_login
        request = RequestFactory().post('/login/login/', {'email':'wrong@example.com', 'password':'wrong', 'role':'user'})
        request.session = self.session
        request._messages = FallbackStorage(request)
        with patch('login.views.Login.objects.filter', return_value=[]), patch('login.views.render') as render:
            add_login(request)
        self.assertEqual(render.call_args.args[2]['msg_type'], 'error')
        self.assertEqual(list(request._messages), [])
