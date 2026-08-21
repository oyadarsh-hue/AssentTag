import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from image.models import Image
from generate.models import Permission
from register.models import Register
from face_utils import get_face_descriptor
import dlib
import cv2
import numpy as np
from assentag import settings

# Find the latest approved permission (likely Neo's consent)
perm = Permission.objects.filter(status='approved').order_by('-per_id').first()

if not perm:
    print("No approved tags found to test.")
    sys.exit()

image_obj = Image.objects.filter(image_id=perm.image_id).first()
if not image_obj:
    print("Image not found.")
    sys.exit()

print(f"Testing regenerate_public_image for Image ID: {image_obj.image_id}")
print(f"Target Approved User: {perm.user_id}")

perms = Permission.objects.filter(image_id=image_obj.image_id)
approved_user_ids = [str(p.user_id) for p in perms if p.status == 'approved']
print(f"All Approved Users for this Image: {approved_user_ids}")

filepath = os.path.join(settings.MEDIA_ROOT, image_obj.photo)
print(f"Loading Base Frame: {filepath}")
base_frame = cv2.imread(filepath)

if base_frame is None:
    print("Failed to load base frame.")
    sys.exit()

public_frame = base_frame.copy()
rgb_frame = cv2.cvtColor(base_frame, cv2.COLOR_BGR2RGB)

detector = dlib.get_frontal_face_detector()
fpath2 = os.path.join(settings.BASE_DIR, settings.STATIC_URL.strip('/'), 'shape_predictor_68_face_landmarks.dat')
predictor = dlib.shape_predictor(fpath2)
fpath3 = os.path.join(settings.BASE_DIR, settings.STATIC_URL.strip('/'), 'dlib_face_recognition_resnet_model_v1.dat')
face_rec_model = dlib.face_recognition_model_v1(fpath3)

faces = detector(rgb_frame)
print(f"Detected {len(faces)} faces in base_frame.")

known_faces = []
for f in Register.objects.all():
    if f.photo:
        ffname = os.path.join(settings.MEDIA_ROOT, f.photo)
        descriptor = get_face_descriptor(ffname)
        if descriptor is not None:
            known_faces.append((str(f.register_id), descriptor))

face_descriptors = []
for face in faces:
    shape = predictor(rgb_frame, face)
    descriptor = face_rec_model.compute_face_descriptor(rgb_frame, shape)
    face_descriptors.append(np.array(descriptor))

allowed_users = set(approved_user_ids)
allowed_users.add(str(image_obj.register_id)) # Uploader is always allowed
print(f"Allowed Users to keep clear: {allowed_users}")

matches = []
for allowed_user in allowed_users:
    allowed_descriptor = None
    for n, desc in known_faces:
        if str(n) == allowed_user:
            allowed_descriptor = desc
            print(f"Found known descriptor for allowed user: {allowed_user}")
            break
    
    if allowed_descriptor is not None:
        for idx, f_desc in enumerate(face_descriptors):
            dist = np.linalg.norm(allowed_descriptor - f_desc)
            print(f"Distance between User {allowed_user} and Face {idx}: {dist}")
            if dist <= 0.6:
                matches.append((dist, allowed_user, idx))

matches.sort(key=lambda x: x[0])

assigned_faces = set()
assigned_users = set()
face_to_user = {}

for dist, allowed_user, f_idx in matches:
    if allowed_user not in assigned_users and f_idx not in assigned_faces:
        face_to_user[f_idx] = (allowed_user, dist)
        assigned_faces.add(f_idx)
        assigned_users.add(allowed_user)
        print(f"Result: Face {f_idx} APPROVED for allowed user {allowed_user} (dist: {dist})")

approved_face_indices = set(face_to_user.keys())
print(f"Final Approved Face Indices: {approved_face_indices}")
