import os, json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

import cv2, dlib, numpy as np
import piexif, piexif.helper
from django.conf import settings
from django.core.cache import cache
from face_utils import get_face_descriptor, face_rec_model, predictor
from image.models import Image
from generate.models import Permission
from register.models import Register

perms = Permission.objects.filter(status='approved')
fixed_count = 0

for perm in perms:
    img_obj = Image.objects.filter(image_id=perm.image_id).first()
    viewer_obj = Register.objects.filter(register_id=perm.user_id).first()
    
    if img_obj and img_obj.photo and viewer_obj and viewer_obj.photo:
        viewer_photo_path = os.path.join(settings.MEDIA_ROOT, viewer_obj.photo)
        filepath = os.path.join(settings.MEDIA_ROOT, img_obj.photo)
        
        if os.path.exists(viewer_photo_path) and os.path.exists(filepath):
            viewer_desc = get_face_descriptor(viewer_photo_path)
            
            try:
                exif_dict = piexif.load(filepath)
                user_comment = exif_dict.get('Exif', {}).get(piexif.ExifIFD.UserComment)
                
                if user_comment and viewer_desc is not None:
                    json_string = piexif.helper.UserComment.load(user_comment)
                    if json_string:
                        json_string = ''.join(c for c in json_string if c.isprintable() and not c.isspace())
                        json_coords = json.loads(json_string)
                        
                        frame = cv2.imread(filepath)
                        if frame is not None:
                            h, w = frame.shape[:2]
                            scale_fac = 400.0 / max(h, w) if max(h, w) > 400 else 1.0
                            if scale_fac != 1.0:
                                frame = cv2.resize(frame, (int(w * scale_fac), int(h * scale_fac)))
                            
                            updated = False
                            for face_data in json_coords:
                                if not face_data.get('user_id'): # Needs to be updated
                                    x = int(face_data['x'] * scale_fac)
                                    y = int(face_data['y'] * scale_fac)
                                    w_face = int(face_data['w'] * scale_fac)
                                    h_face = int(face_data['h'] * scale_fac)
                                    
                                    h_img, w_img = frame.shape[:2]
                                    y1, y2 = max(0, y), min(h_img, y + h_face)
                                    x1, x2 = max(0, x), min(w_img, x + w_face)
                                    
                                    roi_for_eval = frame[y1:y2, x1:x2]
                                    if roi_for_eval.size != 0:
                                        try:
                                            rgb_roi = cv2.cvtColor(roi_for_eval, cv2.COLOR_BGR2RGB)
                                            spoof_rect = dlib.rectangle(0, 0, rgb_roi.shape[1], rgb_roi.shape[0])
                                            shape = predictor(rgb_roi, spoof_rect)
                                            face_desc = np.array(face_rec_model.compute_face_descriptor(rgb_roi, shape))
                                            dist = np.linalg.norm(viewer_desc - face_desc)
                                            
                                            if dist <= 0.56:
                                                face_data['user_id'] = str(perm.user_id)
                                                updated = True
                                                break
                                        except Exception as e:
                                            print(e)
                                            
                            if updated:
                                new_json = json.dumps(json_coords)
                                exif_dict['Exif'][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(new_json)
                                exif_bytes = piexif.dump(exif_dict)
                                piexif.insert(exif_bytes, filepath)
                                fixed_count += 1
                                print(f"Fixed EXIF on Image {img_obj.image_id} for User {perm.user_id}")
            except Exception as e:
                print(f"Error on Image {img_obj.image_id}: {e}")

cache.clear()
print(f"Done! Fixed {fixed_count} retroactive EXIFs.")
