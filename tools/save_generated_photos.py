"""Copy selected generated photographs into the project and optimize for web."""
import json
import shutil
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
manifest = root / (sys.argv[1] if len(sys.argv) > 1 else 'docs/PHOTO_ASSETS.json')
items = json.loads(manifest.read_text(encoding='utf-8'))
for item in items:
    source = Path(item['source'])
    destination = root / item['png']
    if destination.exists() and (root / item['webp']).exists():
        continue
    shutil.copy2(source, destination)
    image = Image.open(source).convert('RGB')
    image.thumbnail((1536, 1024))
    image.save(root / item['webp'], 'WEBP', quality=90, method=6)
    print(item['key'], image.size)
