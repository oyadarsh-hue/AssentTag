import os
import sys
import django
from django.core.files import File
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from image.models import Image

def reseed_photos():
    print("Reseeding test photos...")
    
    # Simulating upload from Neo (register_id = 2)
    new_img1 = Image(
        visibility='public',
        type='public',
        like='0',
        status='approved',
        register_id=2,
        date=datetime.date.today(),
        time=datetime.datetime.now().time()
    )
    # The file group_1772758113.jpeg still exists in static/
    new_img1.photo = 'group_1772758113.jpeg'
    new_img1.choose_file = 'group_1772758113.jpeg'
    new_img1.save()
    print(f"Reseeded Image {new_img1.image_id}")
    
    # Simulating upload from Trinity (register_id = 3)
    new_img2 = Image(
        visibility='public',
        type='public',
        like='0',
        status='approved',
        register_id=3,
        date=datetime.date.today(),
        time=datetime.datetime.now().time()
    )
    # Another test file
    new_img2.photo = 'group_1772758557.jpeg'
    new_img2.choose_file = 'group_1772758557.jpeg'
    new_img2.save()
    print(f"Reseeded Image {new_img2.image_id}")
    
    # Generate generic approved permission tags so the privacy blur activates
    from generate.models import Permission
    Permission.objects.create(image_id=new_img1.image_id, user_id=2, upuser_id=2, status='approved')
    Permission.objects.create(image_id=new_img1.image_id, user_id=3, upuser_id=2, status='approved')
    Permission.objects.create(image_id=new_img2.image_id, user_id=3, upuser_id=3, status='approved')

    print("Reseed complete.")

if __name__ == "__main__":
    reseed_photos()
