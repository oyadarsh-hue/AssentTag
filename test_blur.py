import os
import django
import sys

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

import cv2
import numpy as np
import dlib
from django.conf import settings
from image.models import Image
from register.models import Register
from generate.models import Permission
from face_utils import get_face_descriptor, detector, predictor, face_rec_model

def trace_feed(image_id):
    try:
        ss = 7  # Adarsh's ID based on previous logs
        img_obj = Image.objects.filter(image_id=image_id).first()
        if not img_obj or not img_obj.photo: 
            print("No image object")
            return
            
        filepath = os.path.join(settings.MEDIA_ROOT, img_obj.photo)
        print(f"Reading: {filepath}")
        frame = cv2.imread(filepath)
        if frame is None: 
            print("Frame none")
            return

        h, w = frame.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

        authorized = {str(img_obj.register_id)}
        perms = Permission.objects.filter(image_id=image_id, status='approved')
        for p in perms:
            authorized.add(str(p.user_id))

        known_faces = []
        for uid in authorized:
            u_reg = Register.objects.filter(register_id=uid).first()
            if u_reg and u_reg.photo:
                ffname = os.path.join(settings.MEDIA_ROOT, u_reg.photo)
                if os.path.exists(ffname):
                    desc = get_face_descriptor(ffname)
                    if desc is not None:
                        known_faces.append(desc)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = detector(rgb_frame)
        print(f"Detected {len(faces)} faces.")

        for face in faces:
            is_authorized = False
            try:
                shape = predictor(rgb_frame, face)
                f_desc = np.array(face_rec_model.compute_face_descriptor(rgb_frame, shape))
                print(f"Face {idx} distances:")
                for k_desc in known_faces:
                    dist = np.linalg.norm(k_desc - f_desc)
                    print(f" - to authorized: {dist}")
                    if dist <= 0.48:
                        is_authorized = True
                        break
            except Exception as e:
                print(f"Identification skipped: {e}")

            if not is_authorized: 
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                offset_x, offset_y = int(w * 0.4), int(h * 0.4)
                h_img, w_img = frame.shape[:2]
                y1, y2 = max(0, y - offset_y), min(h_img, y + h + offset_y)
                x1, x2 = max(0, x - offset_x), min(w_img, x + w + offset_x)
                
                roi = frame[y1:y2, x1:x2]
                if roi.size != 0:
                    kw, kh = max(45, int(w*1.5) | 1), max(45, int(h*1.5) | 1)
                    try:
                        blurred_roi = cv2.GaussianBlur(roi, (kw, kh), 0)
                        mask = np.zeros(roi.shape[:2], dtype=np.uint8)
                        cx, cy = (x2 - x1) // 2, (y2 - y1) // 2
                        r = min(cx, cy) - 2
                        if r > 0:
                            cv2.circle(mask, (cx, cy), r, 255, -1)
                            mask_3d = mask[:, :, np.newaxis] / 255.0
                            frame[y1:y2, x1:x2] = (roi * (1 - mask_3d) + blurred_roi * mask_3d).astype(np.uint8)
                        else:
                            frame[y1:y2, x1:x2] = blurred_roi
                    except Exception as e:
                        print(f"Blur mask alignment failed: {e}")
                        try:
                            frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (21, 21), 0)
                        except Exception:
                            pass

        ret, buffer = cv2.imencode('.jpg', frame)
        print(f"Successfully rendered with buffer size {len(buffer)}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

trace_feed(105)
