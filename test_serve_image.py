import os
import sys
import django
from django.test import RequestFactory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from image.views import serve_dynamic_image
from image.models import Image

def test():
    images = Image.objects.all()
    if not images:
        print("No images found in database.")
        return

    factory = RequestFactory()
    for img in images:
        request = factory.get(f'/image/get_media_content/{img.image_id}/', HTTP_HOST='127.0.0.1')
        request.session = {'u_id': img.register_id}

        print(f"Testing serve_dynamic_image for image_id={img.image_id}...")
        try:
            response = serve_dynamic_image(request, img.image_id)
            print(f"Response status: {response.status_code}, Length: {len(response.content)}")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test()
