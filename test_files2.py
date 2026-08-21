import os
import sys
import django
import glob

sys.path.append(r"d:\AssentTag\assentag - Copy (2)")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assentag.settings")
django.setup()

from face_utils import get_face_descriptor

def check_files():
    static_dir = r"d:\AssentTag\assentag - Copy (2)\static"
    # Get all jpg/jpeg files and sort by modification time, newest first
    files = glob.glob(os.path.join(static_dir, "*.jp*"))
    files.sort(key=os.path.getmtime, reverse=True)
    
    print(f"Testing the latest 5 files uploaded...")
    for f in files[:5]:
        print(f"\n--- Checking file: {os.path.basename(f)} ---")
        desc = get_face_descriptor(f)
        if desc is None:
            print("  -> RESULT: None (No face found)")
        else:
            print(f"  -> RESULT: Face DETECTED! Shape: {desc.shape}")

if __name__ == "__main__":
    check_files()
