import os
import sys
import django

sys.path.append(r"d:\AssentTag\assentag - Copy (2)")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assentag.settings")
django.setup()

from face_utils import get_face_descriptor, predictor, face_rec_model

def test_face_utils():
    print("Testing predictor:", predictor)
    print("Testing face_rec_model:", face_rec_model)
    img_path = r"d:\AssentTag\assentag - Copy (2)\static\3.jpg"
    print("Testing real image path:", img_path)
    print("Exists:", os.path.exists(img_path))
    desc = get_face_descriptor(img_path)
    if desc is None:
        print("Result: No face detected or failure.")
    else:
        print("Result: Face detected! Descriptor shape:", desc.shape)
    
if __name__ == "__main__":
    test_face_utils()
