import os
import sys
import django
import glob

sys.path.append(r"d:\AssentTag\assentag - Copy (2)")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assentag.settings")
django.setup()

from face_utils import get_face_descriptor

def test_recent_faces():
    static_dir = r"d:\AssentTag\assentag - Copy (2)\static"
    # Get all jpg/jpeg files and sort by modification time, newest first
    files = glob.glob(os.path.join(static_dir, "*.jp*g"))
    files.sort(key=os.path.getmtime, reverse=True)
    
    print(f"Testing latest 10 files in static...")
    for f in files[:10]:
        print(f"\nTesting file: {os.path.basename(f)}")
        desc = get_face_descriptor(f)
        if desc is None:
            print("  -> RESULT: None")
        else:
            print(f"  -> RESULT: Success! Shape: {desc.shape}")

if __name__ == "__main__":
    test_recent_faces()
