"""Build the public UI showcase without reading the app database or environment.

Run with a Python installation containing Django. Only allowlisted design assets
and fictional fixtures are exported. The actual application is not modified.
"""
from pathlib import Path
import re
import shutil
import django

from django.conf import settings
from django.template import Engine, Context

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
settings.configure(STATIC_URL='static/', USE_TZ=True, SECRET_KEY='static-ui-demo')
django.setup()
engine = Engine(dirs=[ROOT / 'templates', ROOT / 'temp/templates', ROOT / 'login/templates'],
                libraries={'static': 'django.templatetags.static'})

routes = {'/login/login/': 'demo.html#login', '/register/register/': 'demo.html#register',
          '/index/index3/': 'demo.html#feed', '/register/profile/': 'demo.html#profile',
          '/login/messages/': 'messages.html', '/login/chat/2/': 'chat.html',
          '/login/chat/3/': 'chat.html?contact=alex'}

def export(template, filename, context=None):
    html = engine.get_template(template).render(Context(context or {}))
    html = html.replace('/static/', 'static/').replace('/media/', 'static/assets/')
    for source, target in routes.items():
        html = html.replace(source, target)
    html = re.sub(r'<script src="static/js/chat-timers.js" defer></script>',
                  '<script src="demo-chat.js" defer></script>', html)
    html = html.replace('method="POST"', 'method="dialog"')
    html = html.replace('action="chat.html"', '')
    html = html.replace('Applies to both people.', 'UI simulation on this page only.')
    banner = '<div class="demo-notice">UI demo · Fictional sample data <a href="demo.html#feed">Explore the app ↗</a></div>'
    html = html.replace('</head>', '<link rel="stylesheet" href="demo-banner.css"></head>')
    html = html.replace('</body>', banner + '</body>')
    if filename == 'index.html':
        html = html.replace('MILITARY-GRADE SECURITY', 'CONSENT-FIRST SHARING')
        html = html.replace('The only platform that puts you in charge of', 'A project that puts you in charge of')
        html = html.replace('Military-grade biometric authentication.', 'Face-based identity verification.')
        html = html.replace('Real-time threat monitoring, device management, and audit logs. Your data is encrypted at rest and in\n                transit.', 'Explore account verification, privacy decisions, and activity notifications in the interactive UI demo.')
        html = html.replace('Tamper-evident algorithms lock your\n                records permanently.', 'Explore how consent shapes the sharing experience.')
        html = html.replace('Developer API', 'Private Conversations').replace('Seamlessly integrate the AssentTag engine into your third-party infrastructure. Highly documented\n                interoperable limits.', 'Stay connected with mutual friends and choose how long new messages stay with disappearing-message timers.')
        html = html.replace('<p class="hero-desc">', '<div style="margin:20px 0"><a href="demo.html#feed" class="btn-solid">Explore the UI demo ↗</a></div><p class="hero-desc">')
        html = html.replace('</head>', '<meta name="description" content="Explore AssentTag: a consent-based face privacy project. Interactive UI demo with social feed, privacy controls and disappearing messages."><meta property="og:title" content="AssentTag — Your face. Your choice."><meta property="og:description" content="Explore the interactive UI demo of a consent-based face privacy and social sharing project."><meta property="og:image" content="https://oyadarsh-hue.github.io/AssentTag/static/assets/photo-index-hero-v2.webp"></head>')
    (OUT / filename).write_text(html, encoding='utf-8')

OUT.mkdir(exist_ok=True)
assets = OUT / 'static/assets'
assets.mkdir(parents=True, exist_ok=True)
for file in (ROOT / 'static/assets').iterdir():
    if file.suffix == '.webp' or file.name in ('assenttag-logo.png', 'user_icon.svg', 'user_bg.jpg'):
        shutil.copy2(file, assets / file.name)
for kind, names in {'css': ['visual-experience.css', 'chat-timers.css'],
                    'js': ['visual-experience.js', 'success-notices.js']}.items():
    target = OUT / 'static' / kind
    target.mkdir(exist_ok=True)
    for name in names:
        text = (ROOT / 'static' / kind / name).read_text(encoding='utf-8')
        text = text.replace('/static/', 'static/').replace(r'^\/static\/', r'^static\/')
        (target / name).write_text(text, encoding='utf-8')
export('temp/index.html', 'index.html')
people = [dict(register_id=2, first_name='Maya', last_name='River', photo='user_icon.svg'),
          dict(register_id=3, first_name='Alex', last_name='Stone', photo='user_icon.svg')]
export('login/messages.html', 'messages.html', {'current_user': {'first_name': 'Demo', 'photo': 'user_icon.svg'}, 'mutual_users': people})
export('login/chat.html', 'chat.html', {'target_user': people[0], 'timer': {'duration': 86400, 'label': '24 hours'},
       'timer_choices': [(0, 'Off'), (60, '60 seconds'), (86400, '24 hours'), (604800, '7 days'), (7776000, '90 days')]})
for file in (ROOT / 'tools/ui_demo').iterdir():
    shutil.copy2(file, OUT / file.name)
(OUT / '.nojekyll').write_text('', encoding='utf-8')
print('Built UI demo in docs; database and user uploads were not accessed.')
