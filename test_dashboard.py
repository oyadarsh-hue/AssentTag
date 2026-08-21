import os
import sys
import django
import time
from django.test import RequestFactory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from temp.views import add_index3
from register.models import Register

def test():
    user = Register.objects.first()
    if not user:
        print("No users found.")
        return

    factory = RequestFactory()
    request = factory.get(f'/index/index3/')
    request.session = {'u_id': user.register_id, 'type': 'user'}

    print(f"Testing dashboard load for {user.first_name}... ")
    start_time = time.time()
    
    try:
        response = add_index3(request)
        end_time = time.time()
        print(f"Response status: {response.status_code}")
        print(f"Loading time: {end_time - start_time:.4f} seconds!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test()
