import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from register.models import Register, Follower

# Get Adarsh and Alwin
adarsh = Register.objects.filter(email='adarsh23saji@gmail.com').first()
alwin = Register.objects.filter(email='alwinsunil@gmail.com').first()

if adarsh and alwin:
    # Ensure Adarsh follows Alwin
    Follower.objects.get_or_create(follower_user_id=adarsh.register_id, user_id=alwin.register_id)
    # Ensure Alwin follows Adarsh
    Follower.objects.get_or_create(follower_user_id=alwin.register_id, user_id=adarsh.register_id)
    print(f"Mutual follow created between {adarsh.email} ({adarsh.register_id}) and {alwin.email} ({alwin.register_id})")
else:
    print("Could not find one or both users.")

# Let's also print all user IDs
for u in Register.objects.all():
    print(f"User ID: {u.register_id}, Email: {u.email}")
