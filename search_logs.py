import os
import json

search_dir = r"C:\Users\HP\.gemini"
target_strings = ["is_disappearing = models.BooleanField", "backdrop-filter: blur(25px)", "End-to-End Encrypted"]

found_files = []

for root, dirs, files in os.walk(search_dir):
    for str_file in files:
        if str_file.endswith('.json') or str_file.endswith('.txt') or str_file.endswith('.db') or str_file.endswith('.log'):
            filepath = os.path.join(root, str_file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for t in target_strings:
                        if t in content:
                            found_files.append((filepath, t))
                            break
            except Exception:
                pass

for f, t in found_files:
    print(f"Found '{t}' in {f}")
