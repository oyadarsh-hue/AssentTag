from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from django.test import SimpleTestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from image.face_privacy import face_mask, blur_private_face, _forehead_points


class FacePrivacyTests(SimpleTestCase):
    def setUp(self):
        self.frame = np.random.default_rng(6).integers(0, 256, (280,320,3), dtype=np.uint8)
        self.face = dict(x=100,y=80,w=80,h=110)

    @patch('image.face_privacy.predictor', None)
    def test_fallback_covers_features_and_keeps_background(self):
        mask = face_mask(self.frame, self.face)
        self.assertTrue(np.all(mask[100:165,120:160] == 255))
        self.assertEqual(mask[0,0],0)
        # Face shape tapers toward the chin, unlike the previous circular mask.
        self.assertGreater(np.count_nonzero(mask[125]), np.count_nonzero(mask[201]))
        original = self.frame.copy()
        blur_private_face(self.frame,self.face)
        self.assertTrue(np.array_equal(self.frame[mask == 0],original[mask == 0]))
        self.assertLess(self.frame[mask == 255].std(), original[mask == 255].std()/3)

    @patch('image.face_privacy.predictor', side_effect=RuntimeError('unavailable'))
    def test_predictor_failure_still_masks_face(self, predictor):
        self.assertEqual(face_mask(self.frame,self.face)[130,140],255)

    @patch('image.face_privacy.predictor', None)
    def test_edge_faces_are_clipped_without_exposing_center(self):
        for face in [dict(x=-15,y=-5,w=50,h=60),dict(x=295,y=240,w=50,h=60)]:
            mask=face_mask(self.frame,face)
            self.assertGreater(mask.sum(),0)
            blur_private_face(self.frame,face)

    def test_invalid_metadata_fails_closed(self):
        for face in [dict(x=5,y=5,w=0,h=5),dict(x=float('nan'),y=5,w=20,h=20),dict(x=900,y=0,w=20,h=20)]:
            with self.assertRaises(ValueError):
                blur_private_face(self.frame,face)

    def landmark_shape(self, half_width=35, angle=0):
        points=np.tile([140.,140.],(68,1))
        t=np.linspace(np.pi,0,17)
        points[:17]=np.column_stack((140+half_width*np.cos(t),110+80*np.sin(t)))
        points[17:27]=np.column_stack((np.linspace(112,168,10),np.full(10,108)))
        points[36:42]=[124,127]
        points[42:48]=[156,127]
        rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        points=np.rint((points-[140,140])@rotation.T+[140,140]).astype(int)
        shape=SimpleNamespace(part=lambda i:SimpleNamespace(x=int(points[i,0]),y=int(points[i,1])))
        return shape,points

    def test_same_box_adapts_to_different_jaws(self):
        frame=np.full_like(self.frame,150)
        wide,_=self.landmark_shape(38)
        narrow,_=self.landmark_shape(25)
        with patch('image.face_privacy.predictor',return_value=wide):
            wide_mask=face_mask(frame,self.face)
        with patch('image.face_privacy.predictor',return_value=narrow):
            narrow_mask=face_mask(frame,self.face)
        self.assertGreater(np.count_nonzero(wide_mask!=narrow_mask),500)
        self.assertGreater(np.count_nonzero(wide_mask[165]),np.count_nonzero(narrow_mask[165]))

    def test_tilted_face_keeps_all_landmarks_opaque(self):
        shape,points=self.landmark_shape(angle=.32)
        with patch('image.face_privacy.predictor',return_value=shape):
            mask=face_mask(np.full_like(self.frame,150),self.face)
        for x,y in points:
            self.assertEqual(mask[y,x],255)

    def test_spectacle_arms_outside_jaw_are_covered(self):
        shape,_=self.landmark_shape(half_width=35)
        with patch('image.face_privacy.predictor',return_value=shape):
            mask=face_mask(np.full_like(self.frame,150),self.face)
        self.assertEqual(mask[126,100],255)
        self.assertEqual(mask[126,180],255)
        self.assertEqual(mask[190,100],0)  # Do not widen the entire jaw into a fixed shape.

    def test_forehead_tapers_at_temples_without_hair_spikes(self):
        _,points=self.landmark_shape()
        frame=np.full_like(self.frame,150)
        frame[:85]=15  # Distinct hair-to-skin boundary.
        forehead=_forehead_points(frame,points,np.array([0.,1.]),82)
        self.assertGreater(forehead[0,1],forehead[4,1])
        self.assertGreater(forehead[-1,1],forehead[5,1])
        self.assertGreaterEqual(forehead[:,1].min(),79)


class CommentFlowTests(SimpleTestCase):
    def request(self, method='get', content=''):
        request=getattr(RequestFactory(),method)('/image/add_comment/12/',{'comment':content})
        request.session={'u_id':3}
        request._messages=FallbackStorage(request)
        return request

    def test_get_opens_matching_conversation(self):
        from image.views import add_comment
        response=add_comment(self.request(),12)
        self.assertEqual(response.url,'/index/index3/#comments-12')

    def test_post_returns_to_conversation_and_saves_once(self):
        from image.views import add_comment
        with patch('image.views.Image.objects.filter') as images, patch('image.views.CommentPost.objects.create') as create:
            img=SimpleNamespace(image_id=12)
            images.return_value.first.return_value=img
            response=add_comment(self.request('post','  Hello  '),12)
            create.assert_called_once_with(image=img,user_id=3,text='Hello')
            self.assertEqual(response.url,'/index/index3/#comments-12')

    def test_blank_comment_is_not_saved(self):
        from image.views import add_comment
        with patch('image.views.CommentPost.objects.create') as create:
            add_comment(self.request('post','   '),12)
            create.assert_not_called()
