import os
import sys
import django
from django.test import Client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from register.models import Register
from image.models import Image

def test():
    c = Client(SERVER_NAME='127.0.0.1')
    user = Register.objects.first()
    img = Image.objects.order_by('-image_id').first()
    
    session = c.session
    session['u_id'] = user.register_id
    session['type'] = 'user'
    session.save()
    
    url = f'/image/dynamic/feed/{img.image_id}/'
    response = c.get(url)
    
    if response.status_code == 200:
        with open('test_output.jpg', 'wb') as f:
            f.write(response.content)
        print("Image saved to test_output.jpg")
    else:
        print("Error", response.status_code)
        
if __name__ == "__main__":
    test()
