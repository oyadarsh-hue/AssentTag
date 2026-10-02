"""Live browser checks with two temporary accounts; removes only its own data."""
import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.runtime'), str(ROOT)]
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
import django
django.setup()
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
from playwright.async_api import async_playwright
from register.models import Register, Follower, Message


async def verify(users, sessions):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        contexts = []
        pages = []
        errors = []
        for index, session in enumerate(sessions):
            context = await browser.new_context(viewport={'width':1360,'height':960}, reduced_motion='reduce')
            await context.add_cookies([{'name':'sessionid','value':session.session_key,'domain':'127.0.0.1','path':'/'}])
            page = await context.new_page()
            page.on('pageerror',lambda error: errors.append(str(error)))
            response = await page.goto(f'http://127.0.0.1:8010/login/chat/{users[1-index].pk}/',wait_until='networkidle')
            assert response.status == 200
            contexts.append(context)
            pages.append(page)
        a,b = pages
        # Keep one old settings dialog open to exercise stale-save protection.
        await b.get_by_role('button',name='Disappearing messages settings',exact=True).click()
        await a.get_by_role('button',name='Disappearing messages settings',exact=True).click()
        await a.get_by_role('radio',name='1 minute',exact=False).check()
        await a.screenshot(path=str(ROOT/'output/ui/disappearing-settings-desktop.png'))
        await a.get_by_role('button',name='Save timer',exact=True).click()
        await a.wait_for_function("!document.getElementById('timer-dialog').open")
        await b.get_by_role('radio',name='7 days',exact=True).check()
        await b.get_by_role('button',name='Save timer',exact=True).click()
        await b.locator('#timer-error').filter(has_text='another window').wait_for()
        await b.get_by_role('button',name='Cancel',exact=True).click()
        await a.locator('#message-content').fill('Hello there! This is a timed note.')
        await a.get_by_role('button',name='Send',exact=False).click()
        await a.locator('[data-countdown]').wait_for()
        await b.get_by_text('Hello there! This is a timed note.',exact=True).wait_for(timeout=12000)
        await a.reload(wait_until='networkidle')
        assert await a.locator('[data-timer-label]').first.text_content() == '1 minute'
        await a.screenshot(path=str(ROOT/'output/ui/disappearing-countdown-desktop.png'))
        # Off affects only new messages. The pending timer keeps counting down.
        await a.get_by_role('button',name='Disappearing messages settings',exact=True).click()
        await a.get_by_role('radio',name='Off',exact=False).check()
        await a.get_by_role('button',name='Save timer',exact=True).click()
        await a.wait_for_function("!document.getElementById('timer-dialog').open")
        await a.locator('#message-content').fill('This note stays here.')
        await a.get_by_role('button',name='Send',exact=False).click()
        await a.get_by_text('This note stays here.',exact=True).wait_for()
        assert await a.locator('[data-countdown]').count() == 1
        await b.set_viewport_size({'width':390,'height':844})
        await b.screenshot(path=str(ROOT/'output/ui/disappearing-countdown-mobile.png'))
        assert not await b.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
        await b.get_by_role('button',name='Disappearing messages settings',exact=True).click()
        await b.screenshot(path=str(ROOT/'output/ui/disappearing-settings-mobile.png'))
        await b.keyboard.press('Escape')
        # A real one-minute timer, without browser-clock shortcuts.
        await a.get_by_text('Hello there! This is a timed note.',exact=True).wait_for(state='detached',timeout=75000)
        await b.get_by_text('Hello there! This is a timed note.',exact=True).wait_for(state='detached',timeout=12000)
        await a.reload(wait_until='networkidle')
        assert await a.get_by_text('Hello there! This is a timed note.',exact=True).count() == 0
        assert await a.get_by_text('This note stays here.',exact=True).count() == 1
        assert not errors, errors
        print(json.dumps({'desktop':'passed','mobile':'passed','shared_setting':'passed',
                          'stale_save':'passed','real_60_second_expiry':'passed',
                          'off_preserves_existing_deadline':'passed','javascript_errors':errors}))
        await browser.close()


if __name__ == '__main__':
    users, sessions = [], []
    try:
        for name in ('Alex','Maya'):
            now = timezone.now()
            user = Register.objects.create(first_name=name,last_name='Preview',email=f'{uuid4().hex[:12]}@example.invalid',date=now.date(),time=now,status='approved')
            users.append(user)
            session = SessionStore()
            session.update({'u_id':user.pk,'type':'user'})
            session.save()
            sessions.append(session)
        Follower.objects.create(user=users[0],follower_user=users[1])
        Follower.objects.create(user=users[1],follower_user=users[0])
        (ROOT/'output/ui').mkdir(parents=True,exist_ok=True)
        asyncio.run(verify(users,sessions))
        assert Message.objects.filter(sender_id__in=[u.pk for u in users],is_disappearing=True).count() == 0
    finally:
        ids = [u.pk for u in users]
        Message.objects.filter(sender_id__in=ids).delete()
        Follower.objects.filter(user_id__in=ids).delete()
        Follower.objects.filter(follower_user_id__in=ids).delete()
        for session in sessions:
            session.delete()
        Register.objects.filter(pk__in=ids).delete()
