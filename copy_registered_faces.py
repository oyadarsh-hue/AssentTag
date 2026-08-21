import os
import shutil
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
try:
    django.setup()
    from register.models import Register
    
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    
    print(f"Desktop Directory: {desktop_dir}")
    print(f"Static Directory: {static_dir}")
    print("Locating all registered users' anchor photos...")
    
    count = 0
    for user in Register.objects.all():
        # Try reg_photo, fall back to photo
        photo_field = getattr(user, 'reg_photo', None) or getattr(user, 'photo', None)
        if photo_field:
            photo_name = str(photo_field)
            source_path = os.path.join(static_dir, photo_name)
            if os.path.exists(source_path):
                # Clean up filename by replacing slashes with underscores to keep it flat
                clean_filename = photo_name.replace("/", "_").replace("\\", "_")
                dest_path = os.path.join(desktop_dir, f"registered_user_{user.register_id}_{clean_filename}")
                shutil.copy(source_path, dest_path)
                print(f"Copied: {photo_name} -> {dest_path}")
                count += 1
            else:
                print(f"Photo path does not exist: {source_path}")
        else:
            print(f"User ID {user.register_id} has no profile photo associated.")
            
    print(f"\nDone! Copied {count} registered user profile/anchor photos to your Desktop.")
except Exception as e:
    print(f"Error running django model query: {e}")
