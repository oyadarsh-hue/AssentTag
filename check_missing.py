import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from image.models import Image
from django.conf import settings

deleted = 0
for img in Image.objects.filter(photo__isnull=False):
    filepath = os.path.join(settings.MEDIA_ROOT, img.photo)
    if not os.path.exists(filepath):
        print(f"Deleting phantom record: {img.image_id} - {img.photo}")
        img.delete()
        deleted += 1

print(f"Total phantom records deleted: {deleted}")
