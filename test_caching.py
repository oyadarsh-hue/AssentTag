import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assentag.settings")
django.setup()

from assentag import settings
from face_utils import get_face_descriptor

def test_cache():
    media_dir = settings.MEDIA_ROOT
    images = [f for f in os.listdir(media_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not images:
        print("No images found to test.")
        return
        
    print(f"Testing caching on {len(images)} images in: {media_dir}")
    
    # First run: should compute (slow)
    start_time = time.time()
    for img in images:
        get_face_descriptor(os.path.join(media_dir, img))
    end_time = time.time()
    first_run_time = end_time - start_time
    print(f"First run (computing): {first_run_time:.4f} seconds")
    
    # Second run: should fetch from cache (very fast)
    start_time = time.time()
    for img in images:
        get_face_descriptor(os.path.join(media_dir, img))
    end_time = time.time()
    second_run_time = end_time - start_time
    print(f"Second run (cached): {second_run_time:.4f} seconds")

if __name__ == "__main__":
    test_cache()
