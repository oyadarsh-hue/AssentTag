import base64
from contextlib import ExitStack
from unittest.mock import Mock, patch
import numpy as np
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import SimpleTestCase, RequestFactory
from register.views import add_register1


class RegistrationNoticeTests(SimpleTestCase):
    def request(self):
        request = RequestFactory().post('/register/register/', {
            'fname':'Alex', 'lname':'Example', 'email':'example@example.com',
            'pass':'Example123!', 'cpass':'Example123!',
            'photo':SimpleUploadedFile('portrait.jpg', b'isolated-test-photo'),
            'live_photo':'data:image/jpeg;base64,' + base64.b64encode(b'isolated-capture').decode(),
        })
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        return request

    def test_registration_success_is_delivered_after_redirect(self):
        request = self.request()
        descriptor = np.array([.1,.2,.3])
        face = Mock()
        face.width.return_value = face.height.return_value = 10
        with ExitStack() as stack:
            users = stack.enter_context(patch('register.views.Register'))
            users.objects.all.return_value = []
            users.return_value.register_id = 37
            accounts = stack.enter_context(patch('register.views.Login'))
            storage = stack.enter_context(patch('register.views.FileSystemStorage'))
            storage.return_value.save.return_value = 'isolated-photo.jpg'
            stack.enter_context(patch('register.views.get_face_descriptor', return_value=descriptor))
            stack.enter_context(patch('register.views.compare_faces', return_value=('Unknown',0)))
            stack.enter_context(patch('face_utils.detector', return_value=[face]))
            stack.enter_context(patch('face_utils.predictor'))
            model = stack.enter_context(patch('face_utils.face_rec_model'))
            model.compute_face_descriptor.return_value = descriptor
            stack.enter_context(patch('cv2.imdecode', return_value=np.zeros((2,2,3),dtype=np.uint8)))
            stack.enter_context(patch('cv2.imwrite', return_value=True))
            stack.enter_context(patch('builtins.print'))
            response = add_register1(request)
            users.return_value.save.assert_called_once()
            accounts.return_value.save.assert_called_once()
        self.assertEqual(response.url, '/login/login/')
        queued = list(request._messages)
        self.assertEqual(len(queued),1)
        self.assertIn('registration',queued[0].tags)
        self.assertEqual(queued[0].level,messages.SUCCESS)

    def test_registration_failure_does_not_queue_success(self):
        request = self.request()
        request.POST = request.POST.copy()
        request.POST['cpass'] = 'Different123!'
        with patch('register.views.render') as render:
            add_register1(request)
        self.assertEqual(render.call_args.args[2]['msg_type'],'error')
        self.assertEqual(list(request._messages),[])

    def test_popup_text_is_escaped_in_shared_template(self):
        request = self.request()
        messages.success(request, '<img src=x onerror="alert(1)">', extra_tags='registration')
        markup = render_to_string('includes/success-notices.html',request=request)
        self.assertNotIn('<img',markup)
        self.assertIn('&lt;img',markup)
