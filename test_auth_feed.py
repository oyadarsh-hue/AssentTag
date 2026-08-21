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
    if not user:
        print("No users in DB.")
        return
        
    img = Image.objects.order_by('-image_id').first()
    if not img:
        print("No images in DB.")
        return
        
    session = c.session
    session['u_id'] = user.register_id
    session['type'] = 'user'
    session.save()
    
    url = f'/image/dynamic/feed/{img.image_id}/'
    print(f"Requesting {url} as user {user.register_id}")
    response = c.get(url)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 500:
        print("500 error detected!")
    else:
        print(f"Content length: {len(response.content)}")
    
if __name__ == "__main__":
    test()
