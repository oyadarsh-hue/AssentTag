import os
import shutil

base_dir = r"d:\AssentTag\assentag - Copy (2)"
for root, dirs, files in os.walk(base_dir, topdown=False):
    if "__pycache__" in dirs:
        cache_dir = os.path.join(root, "__pycache__")
        try:
            shutil.rmtree(cache_dir)
            print(f"Deleted {cache_dir}")
        except Exception as e:
            print(f"Error {cache_dir}: {e}")
