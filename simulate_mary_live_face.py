import os
import shutil
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')

try:
    django.setup()
    from register.models import Register
    
    # Locate Mary JB (ID: 10)
    user = Register.objects.filter(register_id=10).first()
    if user and user.reg_photo:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        
        source_path = os.path.join(static_dir, str(user.reg_photo))
        
        if os.path.exists(source_path):
            # Create a simulated live face verification file name
            dest_path = os.path.join(desktop_dir, f"live_verified_face_10_maryjb.jpg")
            shutil.copy(source_path, dest_path)
            print(f"SUCCESS: Simulated Mary JB's live face verification capture!")
            print(f"Copied from: {source_path}")
            print(f"Saved to Desktop: {dest_path}")
        else:
            print(f"Error: Profile photo file not found at: {source_path}")
    else:
        print("Error: Mary JB (ID: 10) not found or has no reference photo in the database.")
        
except Exception as e:
    print(f"Error simulating verification: {e}")
