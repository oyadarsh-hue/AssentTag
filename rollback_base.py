import os
import shutil

src_dir = r"d:\AssentTag\assentag"
dst_dir = r"d:\AssentTag\assentag - Copy (2)"

# List of Django apps containing templates
apps = ['login', 'register', 'temp', 'feedback', 'image', 'complaint']

for app in apps:
    src_templates = os.path.join(src_dir, app, 'templates', app)
    dst_templates = os.path.join(dst_dir, app, 'templates', app)
    
    if os.path.exists(src_templates):
        # We need to overwrite the monolithic files with the original UI base files
        shutil.copytree(src_templates, dst_templates, dirs_exist_ok=True)

# Also ensure index.html gets restored just in case it's in temp
src_temp = os.path.join(src_dir, 'temp', 'templates', 'temp')
dst_temp = os.path.join(dst_dir, 'temp', 'templates', 'temp')
if os.path.exists(src_temp):
     shutil.copytree(src_temp, dst_temp, dirs_exist_ok=True)

print("Rollback to Base HTML complete.")
