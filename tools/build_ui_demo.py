"""Export original project templates and animations with fictional fixtures.

This standalone exporter never loads application settings, database or uploads.
"""
from pathlib import Path
from datetime import date, time
import json
import re
import shutil
import django
from django.conf import settings
from django.template import Engine, Context

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
settings.configure(STATIC_URL='static/', USE_TZ=True, SECRET_KEY='static-ui-demo')
django.setup()
engine = Engine(dirs=[ROOT/'templates'] + list(ROOT.glob('*/templates')),
                libraries={'static':'django.templatetags.static'})
names = [('Jamie','Demo'),('Maya','River'),('Alex','Stone'),('Robin','Kay'),('Sam','Lee'),('Taylor','Sky')]
people = [dict(register_id=i+1,first_name=first,last_name=last,email=f'{first.lower()}@example.com',
               photo='assets/user_icon.svg',date=date(2026,1,1),time=time(10),date_of_birth=date(2000,1,1),
               gender='Not specified',city='Sample city',country='India',mobile='Not provided',
               bio='Fictional profile for the public UI preview.',is_private=False,status='approved')
          for i,(first,last) in enumerate(names)]
posts = [dict(image_id=i+1,register=people[i+1],register_id=i+2,photo=f'assets/{image}.webp',
              date='2026-01-01',time='10:30',type='image',caption=caption,tags=['SharedWithConsent'],
              like_count=12+i,has_liked=False,recent_comments=[],is_ghost_text=False,likes={'count':12+i})
         for i,(image,caption) in enumerate([('photo-index-hero-v2','A moment shared thoughtfully.'),
             ('page-dashboard-moments','Small moments with good company.'),('photo-consent','Every face has a say.'),
             ('page-stories','A new story every day.')])]
ghost=dict(posts[0],image_id=5,is_ghost_text=True,text_content='Your face. Your choice.',caption='Hold to read this sample Ghost Text.')
feed=[posts[0],ghost,*posts[1:]]
base=dict(current_user=people[0],j=people[0],a=feed,user_posts=posts,stories=posts[:2],
          user_posts_count=4,followers_count=3,following_count=2,followers_list=people[1:4],following_list=people[1:3],
          following_ids_list=[2,3],suggestions=people[3:],all_users=people[1:],friends=people[1:3],
          notif_count=1,can_view_posts=True,is_following=True,followers=[{'follower_user':p} for p in people[1:4]],
          following=[{'user':p} for p in people[1:3]],u=[dict(per_id=1,image_id=1,image=posts[0])],
          follow_requests=[],request={'session':{'u_id':1,'type':'user'}})
routes={'/index/index3/':'demo.html','/index/index/':'index.html','/index/index1/':'module.html',
        '/index/index2/':'admin.html','/index/index4/':'notifications.html','/index/explore/':'explore.html',
        '/login/login/':'login.html','/register/register/':'register.html','/register/profile/':'profile.html',
        '/login/messages/':'messages.html','/image/image/':'upload.html','/image/add_story/':'add-story.html',
        '/complaint/complaint/':'complaint.html','/complaint/view_replies/':'replies.html','/feedback/feedback/':'feedback.html',
        '/register/individual-user/':'members.html','/image/view/':'media.html','/complaint/view/':'admin-complaints.html',
        '/feedback/view/':'admin-feedback.html','/register/deactivate/':'#demo-action-deactivate',
        '/register/scorched_earth/':'#demo-action-delete-account','/image/review-tag/1/':'verify.html'}
for p in people:
    i=p['register_id']
    routes.update({f'/register/u_view_profile/{i}/':f'profile-{i}.html',f'/register/edit/{i}/':'edit-profile.html',f'/login/chat/{i}/':f'chat-{i}.html'})
for p in feed:
    routes[f"/image/content/media/{p['image_id']}/"]=f"static/{p['photo']}"
    routes[f"/image/view_story/{p['image_id']}/"]='story.html'

def rewrite(text):
    text=re.sub(r'/image/content/notif/\d+/\d+/\?t=\d+','static/assets/photo-protection.webp',text)
    text=re.sub(r'/image/content/profile/\d+/','static/assets/user_icon.svg',text)
    for source,target in sorted(routes.items(),key=lambda kv:-len(kv[0])):
        text=text.replace(source,target)
        text=re.sub(re.escape(source.rstrip('/'))+r'(?=[\x22\x27])',lambda m:target,text)
    text=text.replace('/register/u_view_profile/${user.register_id}/','profile-${user.register_id}.html')
    text=re.sub(r'/(?:login/(?:follow|unfollow|remove_follower|accept_follow|reject_follow)|image/(?:like-post|delete-comment|delete_post|approve-tag|reject-tag)|register/(?:accept|reject))/(\d+)/',lambda m:'#demo-action-'+m[0].strip('/').replace('/','-'),text)
    text=text.replace("window.location.origin + 'demo.html", "new URL('demo.html', location.href).href + '")
    text=text.replace('/static/','static/').replace('/media/','static/')
    for missing in ['default.jpg','default_avatar.jpg','default_user.png','back.jpg']:
        text=text.replace('static/assets/'+missing,'static/assets/user_icon.svg')
    return text

def prepare_input(match):
    tag=match[0]
    name=re.search(r'name=[\x22\x27]([^\x22\x27]+)',tag)
    values={'email':'jamie@example.com','password':'DemoOnly123!','cpassword':'DemoOnly123!','pass':'DemoOnly123!','cpass':'DemoOnly123!',
            'confirm_password':'DemoOnly123!','fname':'Jamie','lname':'Demo','dob':'2000-01-01','mobile':'0000000000','city':'Sample city'}
    if name and name[1] in values:
        tag=re.sub(r'\svalue="[^"]*"','',tag).replace(' readonly','')
        tag=tag.replace('>',f' value="{values[name[1]]}" readonly>')
    return tag

manifest={}
def export(template,filename,extra=None):
    source=engine.get_template(template).render(Context({**base,**(extra or {})}))
    text=rewrite(source).replace('data-site-mode="app"', 'data-site-mode="preview"')
    text=re.sub(r'<form\b([^>]*)>',lambda m:'<form'+re.sub(r'\s(?:action|method)="[^"]*"','',m[1])+' method="dialog" novalidate data-demo-form>',text)
    if filename in ('login.html','register.html','edit-profile.html'):
        text=re.sub(r'<input\b[^>]*>',prepare_input,text)
    text=text.replace('<script src="static/js/chat-timers.js" defer></script>','<script src="demo-chat.js" defer></script>')
    if filename=='verify.html':
        # Its script is entirely webcam authentication; preserve its scanner CSS.
        text=re.sub(r'<script>.*?</script>','',text,flags=re.S)
        text=text.replace('Initializing camera...','UI preview · Camera and identity verification are disabled.')
    text=text.replace('<head>','<head>\n<script src="demo-adapter.js"></script>')
    text=text.replace('</head>','<link rel="stylesheet" href="demo-banner.css"></head>')
    text=text.replace('</body>','<div class="demo-notice" role="note">UI preview · Sample data <a href="demo.html">Dashboard ↗</a><button type="button" aria-label="Dismiss demo notice" onclick="this.parentElement.remove()">×</button></div></body>')
    text='\n'.join(line.rstrip() for line in text.splitlines())+'\n'
    (OUT/filename).write_text(text,encoding='utf-8')
    styles=lambda v:re.findall(r'<style[^>]*>(.*?)</style>',v,re.S)
    assert [s.strip() for s in styles(text)]==[s.strip() for s in styles('\n'.join(l.rstrip() for l in rewrite(source).splitlines()))],filename
    manifest[filename]=template

OUT.mkdir(exist_ok=True)
assets=OUT/'static/assets'
assets.mkdir(parents=True,exist_ok=True)
for file in (ROOT/'static/assets').iterdir():
    if file.suffix=='.webp' or file.name in ('assenttag-logo.png','user_icon.svg','user_bg.jpg','admin_bg.jpg','admin_icon.svg','style.css','script.js','background.svg','world_map.svg','hero-face.jpg'):
        shutil.copy2(file,assets/file.name)
        if file.suffix=='.svg':
            (assets/file.name).write_text('\n'.join(line.rstrip() for line in file.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
for kind,names in {'css':['visual-experience.css','color-vibe.css','chat-timers.css','assistant.css'],'js':['visual-experience.js','success-notices.js','assistant-config.js','assistant.js']}.items():
    target=OUT/'static'/kind
    target.mkdir(exist_ok=True)
    for name in names:
        text=(ROOT/'static'/kind/name).read_text(encoding='utf-8')
        (target/name).write_text(text.replace('/static/','static/').replace(r'^\/static\/',r'^static\/'),encoding='utf-8')

for template,filename,extra in [
    ('temp/index.html','index.html',{}),('temp/dashboard.html','demo.html',{}),
    ('temp/explore_feed.html','explore.html',{}),('temp/user_home.html','module.html',{}),('temp/admin_home.html','admin.html',{}),
    ('login/login.html','login.html',{}),('register/register.html','register.html',{}),
    ('register/u_view_profile.html','profile.html',{}),('register/profile-edit.html','edit-profile.html',{}),
    ('image/user-upload.html','upload.html',{}),('image/user_story_upload.html','add-story.html',{}),
    ('image/view_story.html','story.html',{'story':posts[0],'next_story_url':'demo.html','prev_story_url':'demo.html'}),
    ('temp/notifications.html','notifications.html',{}),('temp/verify_tag.html','verify.html',{'perm_id':1}),
    ('login/messages.html','messages.html',{'mutual_users':people[1:3]}),('complaint/user_complaint.html','complaint.html',{}),
    ('complaint/view_replies.html','replies.html',{}),('feedback/user_feedback.html','feedback.html',{}),
    ('register/individual-users.html','members.html',{'a':people}),('image/admin_photo_details.html','media.html',{'a':posts}),
    ('complaint/admin_complaints_view.html','admin-complaints.html',{'a':[]}),('feedback/admin_feedback_view.html','admin-feedback.html',{'a':[]})]:
    export(template,filename,extra)
story_file=OUT/'story.html'
story_file.write_text(story_file.read_text(encoding='utf-8').replace('data:image/jpeg;base64,','static/assets/page-stories.webp'),encoding='utf-8')
for person in people:
    export('register/public_profile.html',f"profile-{person['register_id']}.html",{'j':person})
    export('login/chat.html',f"chat-{person['register_id']}.html",{'target_user':person,'timer':{'duration':86400,'label':'24 hours'},
        'timer_choices':[(0,'Off'),(60,'60 seconds'),(86400,'24 hours'),(604800,'7 days'),(7776000,'90 days')]})
shutil.copy2(OUT/'chat-2.html',OUT/'chat.html')
for file in (ROOT/'tools/ui_demo').iterdir():
    shutil.copy2(file,OUT/file.name)
(OUT/'.nojekyll').write_text('',encoding='utf-8')
(OUT/'ui-template-map.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(f'Exported {len(manifest)} original templates with original inline CSS and visual scripts.')
