"""Read-only UI verification; creates and removes its own login session."""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.runtime'), str(ROOT)]
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
import django
django.setup()
from django.contrib.sessions.backends.db import SessionStore
from register.models import Register
from playwright.async_api import async_playwright


async def verify(session):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
        await context.add_cookies([{'name':'sessionid','value':session.session_key,'domain':'127.0.0.1','path':'/'}])
        page = await context.new_page()
        errors=[]
        page.on('pageerror',lambda error: errors.append(str(error)))
        await page.goto('http://127.0.0.1:8010/index/index3/',wait_until='domcontentloaded')
        post=page.locator('.post-card').first
        button=post.locator('[data-comments]')
        panel_id=await button.get_attribute('data-comments')
        panel=page.locator('#'+panel_id)
        assert not await panel.is_visible()
        url=page.url
        await button.click()
        assert page.url==url and await panel.is_visible()
        assert await button.get_attribute('aria-expanded')=='true'
        assert await panel.locator('input[name="comment"]').evaluate('(el)=>el===document.activeElement')
        await button.click()
        assert not await panel.is_visible()
        await button.focus()
        await page.keyboard.press('Enter')
        assert await panel.is_visible()
        await post.screenshot(path=str(ROOT/'output/ui/post-actions-desktop.png'))
        # Existing comment URLs also open the correct conversation after redirect.
        post_id=panel_id.removeprefix('comments-')
        await page.goto(f'http://127.0.0.1:8010/image/add_comment/{post_id}/',wait_until='domcontentloaded')
        await page.wait_for_selector('#'+panel_id,state='visible')
        assert page.url.endswith('#'+panel_id)
        await page.set_viewport_size({'width':390,'height':844})
        await post.screenshot(path=str(ROOT/'output/ui/post-actions-mobile.png'))
        assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
        # Inspect the real processed photo endpoint, without changing any consent.
        photo=page.locator('.post-image[src^="/image/content/media/"]').first
        await photo.evaluate('(img)=>img.decode()')
        assert await photo.evaluate('(img)=>img.naturalWidth>0')
        await photo.screenshot(path=str(ROOT/'output/ui/face-shaped-privacy.png'))
        assert not errors,errors
        print(json.dumps({'comment_toggle':'passed','keyboard_focus':'passed','comment_redirect':'passed','mobile_overflow':False,'processed_photo':'loaded','javascript_errors':errors}))
        await browser.close()


if __name__=='__main__':
    user=Register.objects.filter(email__iexact='adarsh22saji@gmail.com').first()
    session=SessionStore()
    session.update({'u_id':user.register_id,'type':'user'})
    session.save()
    try:
        asyncio.run(verify(session))
    finally:
        session.delete()
