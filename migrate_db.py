import os
import sys
import django
from django.db import connection

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

def add_reg_photo_col():
    try:
        with connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM `register` LIKE 'reg_photo'")
            result = cursor.fetchone()
            if not result:
                print("Adding reg_photo column...")
                cursor.execute("ALTER TABLE register ADD COLUMN reg_photo VARCHAR(200) NULL;")
                
                # Copy existing photo data into reg_photo as the baseline anchor
                cursor.execute("UPDATE register SET reg_photo = photo WHERE reg_photo IS NULL;")
                print("Column added and backfilled successfully!")
            else:
                print("Column 'reg_photo' already exists.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_reg_photo_col()
