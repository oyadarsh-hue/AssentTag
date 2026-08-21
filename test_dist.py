import os
import sys
import django
import glob
import numpy as np

sys.path.append(r"d:\AssentTag\assentag - Copy (2)")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assentag.settings")
django.setup()

from face_utils import get_face_descriptor

def check_distances():
    static_dir = r"d:\AssentTag\assentag - Copy (2)\static"
    files = glob.glob(os.path.join(static_dir, "*.jp*"))
    files.sort(key=os.path.getmtime, reverse=True)
    
    # get latest 2 images with faces
    face_files = []
    descs = []
    
    for f in files:
        if "live" in f: continue # skip blank live photos
        desc = get_face_descriptor(f)
        if desc is not None:
            face_files.append(os.path.basename(f))
            descs.append(desc)
        if len(descs) == 3:
            break
            
    if len(descs) >= 2:
        dist01 = np.linalg.norm(descs[0] - descs[1])
        dist02 = np.linalg.norm(descs[0] - descs[2])
        dist12 = np.linalg.norm(descs[1] - descs[2])
        print(f"Distance between {face_files[0]} and {face_files[1]}: {dist01}")
        print(f"Distance between {face_files[0]} and {face_files[2]}: {dist02}")
        print(f"Distance between {face_files[1]} and {face_files[2]}: {dist12}")

if __name__ == "__main__":
    check_distances()
