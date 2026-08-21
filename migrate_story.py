import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from django.db import connection

def migrate():
    with connection.cursor() as cursor:
        try:
            cursor.execute("ALTER TABLE image ADD COLUMN is_story TINYINT(1) DEFAULT 0;")
            print("Successfully added 'is_story' column to 'image' table.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("Column 'is_story' already exists. Skipping.")
            else:
                print(f"Error: {e}")

if __name__ == '__main__':
    migrate()
