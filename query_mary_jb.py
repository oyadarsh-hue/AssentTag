import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')

try:
    django.setup()
    from register.models import Register
    from image.models import Image
    from generate.models import Permission
    
    # 1. Look up Mary JB (ID: 10)
    user = Register.objects.filter(register_id=10).first()
    if user:
        print("="*60)
        print("                 MARY JB (ID: 10) USER ACCOUNT DETAILS")
        print("="*60)
        print(f"Name                : {user.first_name} {user.last_name}")
        print(f"Email               : {user.email}")
        print(f"Status              : {user.status}")
        print(f"Photo Field (photo) : {user.photo}")
        print(f"Anchor Field (reg)  : {user.reg_photo}")
        
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        photo_path = os.path.join(static_dir, str(user.photo)) if user.photo else None
        reg_path = os.path.join(static_dir, str(user.reg_photo)) if user.reg_photo else None
        
        print(f"Profile Image File Path on disk : {photo_path} (Exists: {os.path.exists(photo_path) if photo_path else False})")
        print(f"Anchor Image File Path on disk  : {reg_path} (Exists: {os.path.exists(reg_path) if reg_path else False})")
        
        # 2. Look up tags / permissions for Mary JB
        print("\n" + "="*60)
        print("                 MARY JB TAGS & PERMISSIONS")
        print("="*60)
        perms = Permission.objects.filter(user_id=10)
        print(f"Found {perms.count()} permission records:")
        for p in perms:
            print(f"  [+] Perm ID: {p.per_id} | Image ID: {p.image_id} | Status: {p.status} | Uploader ID: {p.upuser_id}")
            
    else:
        print("User with ID 10 (Mary JB) not found in the database.")
        
except Exception as e:
    print(f"Error querying database: {e}")
