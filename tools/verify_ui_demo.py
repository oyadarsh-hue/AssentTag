"""Check static export resources, navigation and inline JavaScript syntax."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]/'docs'
errors=[]
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key not in ('src','href','action') or not value or value.startswith('#'): continue
            url=urlsplit(value)
            if url.scheme or url.netloc: continue
            if url.path.startswith('/') or not (ROOT/url.path).is_file():
                errors.append(f'{file.name}: invalid {key}: {value}')
for file in ROOT.glob('*.html'):
    text=file.read_text(encoding='utf-8')
    Links().feed(text)
    if '{%' in text or '{{' in text: errors.append(f'{file.name}: unrendered template')
    for index,script in enumerate(re.findall(r'<script\b([^>]*)>(.*?)</script>',text,re.S)):
        attrs,code=script
        if 'application/json' in attrs or not code.strip():continue
        with tempfile.NamedTemporaryFile(mode='w',suffix='.js',encoding='utf-8',delete=False) as js:
            js.write(code);name=js.name
        result=subprocess.run(['node','--check',name],capture_output=True,text=True)
        Path(name).unlink()
        if result.returncode:errors.append(f'{file.name} script {index}: {result.stderr}')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('All exported resources, navigation and inline scripts validated.')
