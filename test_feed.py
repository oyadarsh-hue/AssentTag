import os
import sys
import django
from django.test import RequestFactory

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from image.views import serve_dynamic_image
from image.models import Image

def test():
    # Find newest image
    img = Image.objects.order_by('-image_id').first()
    if not img:
        print("No image found in DB.")
        return

    print(f"Testing serve_dynamic_image with image_id={img.image_id}, photo={img.photo}")
    
    factory = RequestFactory()
    request = factory.get(f'/image/dynamic/feed/{img.image_id}/')
    # Mock session
    request.session = {'u_id': img.register_id}

    response = serve_dynamic_image(request, img.image_id)
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print("Failed to get 200 OK.")

if __name__ == '__main__':
    test()
