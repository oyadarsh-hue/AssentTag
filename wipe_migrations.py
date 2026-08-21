import os

base_dir = r"d:\AssentTag\assentag - Copy (2)"
for root, dirs, files in os.walk(base_dir):
    if "migrations" in root.split(os.sep) and "__pycache__" not in root:
        for file in files:
            if file != "__init__.py" and file.endswith(".py"):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Deleted {file_path}")
