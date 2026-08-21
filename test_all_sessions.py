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
    img = Image.objects.order_by('-image_id').first()
    if not img:
        print("No images in DB.")
        return
        
    users = Register.objects.all()
    for user in users:
        c = Client(SERVER_NAME='127.0.0.1')
        session = c.session
        session['u_id'] = user.register_id
        session['type'] = 'user'
        session.save()
        
        url = f'/image/dynamic/feed/{img.image_id}/'
        response = c.get(url)
        
        print(f"User {user.register_id} ({user.first_name}): Status {response.status_code}, Length: {len(response.content) if response.status_code == 200 else 'N/A'}")
        
if __name__ == "__main__":
    test()
