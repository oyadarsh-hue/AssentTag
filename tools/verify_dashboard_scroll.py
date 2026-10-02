"""Check the new dashboard photography and local success dialogs without user mutations."""
import asyncio
from types import SimpleNamespace
from verify_visual_pages import ROOT, make_session, async_playwright
from django.contrib.messages import SUCCESS
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse


def queue_notice(session_key, tags, text):
    session = SessionStore(session_key)
    storage = FallbackStorage(SimpleNamespace(session=session,COOKIES={}))
    storage.add(SUCCESS,text,extra_tags=tags)
    response = HttpResponse()
    storage.update(response)
    session.save()
    return [{'name':key,'value':cookie.value,'domain':'127.0.0.1','path':'/'} for key,cookie in response.cookies.items()]


async def verify(sessions):
    output = ROOT / 'output/ui'
    output.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width':1440,'height':1000})
        await context.route('**/*sweetalert*',lambda route:route.abort())
        page = await context.new_page()
        errors = []
        page.on('pageerror',lambda error:errors.append(str(error)))
        cookie = lambda role:{'name':'sessionid','value':sessions[role].session_key,'domain':'127.0.0.1','path':'/'}
        await context.add_cookies([cookie('user')])
        await page.goto('http://127.0.0.1:8010/index/index3/',wait_until='domcontentloaded')
        cards = page.locator('.at-dashboard-scene')
        assert await cards.count() == 3
        assert await cards.evaluate_all('(cards) => new Set(cards.map(c => c.dataset.workflowImage)).size === 3')
        sources = await cards.evaluate_all('(cards) => cards.map(c => c.dataset.workflowImage)')
        for index, card in enumerate(await cards.all()):
            await card.evaluate('(el) => el.scrollIntoView({block:"center",behavior:"instant"})')
            await card.locator('img').evaluate('(img) => img.decode()')
            await page.wait_for_timeout(1200)
            assert await card.evaluate('(el) => el.classList.contains("at-revealed")')
            assert await page.locator('.at-scene-layer.is-active').evaluate('(el, src) => el.style.backgroundImage.includes(src)',sources[index])
            before = await card.evaluate('(el) => el.style.getPropertyValue("--at-photo-shift")')
            await page.evaluate('scrollBy({top:100,behavior:"instant"})')
            await page.wait_for_timeout(200)
            after = await card.evaluate('(el) => el.style.getPropertyValue("--at-photo-shift")')
            assert before and after and before != after, 'Photography must move with scrolling'
            await card.screenshot(path=str(output / f'dashboard-scroll-{index+1}.png'))
        await page.evaluate('scrollTo({top:0,behavior:"instant"})')
        await page.wait_for_timeout(300)
        assert not await cards.first.evaluate('(el) => el.classList.contains("at-revealed")')
        await cards.first.evaluate('(el) => el.scrollIntoView({block:"center",behavior:"instant"})')
        await page.wait_for_timeout(1100)
        assert await cards.first.evaluate('(el) => el.classList.contains("at-revealed")')
        await page.set_viewport_size({'width':390,'height':844})
        for card in await cards.all():
            await card.evaluate('(el) => el.scrollIntoView({block:"center",behavior:"instant"})')
            await page.wait_for_timeout(1100)
            assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
        await cards.last.screenshot(path=str(output / 'dashboard-scroll-mobile.png'))
        await page.emulate_media(reduced_motion='reduce')
        assert await cards.last.locator('img').evaluate('(img) => getComputedStyle(img).transform === "none"')
        await page.emulate_media(reduced_motion='no-preference')
        for role, tags, path, title in [
            ('user','login','/index/index3/','Login successful'),
            ('user','registration','/login/login/','Registration successful'),
            ('admin','admin-login','/index/index2/','Admin login successful'),
        ]:
            notice_cookies = await asyncio.to_thread(queue_notice,sessions[role].session_key,tags,'Your action was completed successfully.')
            await context.add_cookies([cookie(role),*notice_cookies])
            await page.goto('http://127.0.0.1:8010' + path,wait_until='domcontentloaded')
            dialog = page.locator('.at-success-dialog')
            await dialog.wait_for(state='visible')
            await page.wait_for_timeout(1000)
            assert await dialog.locator('h2').inner_text() == title
            assert await dialog.evaluate('(el) => el.contains(document.activeElement)')
            assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
            await page.screenshot(path=str(output / f'success-{tags}-mobile.png'))
            await dialog.locator('.at-success-confirm').click()
            await dialog.wait_for(state='detached')
            await page.reload(wait_until='domcontentloaded')
            await page.wait_for_timeout(300)
            assert await page.locator('.at-success-dialog').count() == 0, 'Success should be shown once'
        await page.evaluate('window.AssentTagNotice.success("<img src=x onerror=window.badPopup=true>", {title:"Safe message"})')
        await page.locator('.at-success-dialog').wait_for(state='visible')
        assert await page.locator('.at-success-dialog #at-success-message').inner_text() == '<img src=x onerror=window.badPopup=true>'
        assert await page.locator('.at-success-dialog img[src="x"]').count() == 0
        await page.keyboard.press('Escape')
        await page.locator('.at-success-dialog').wait_for(state='detached')
        assert not await page.locator('body').evaluate('(body) => body.classList.contains("at-success-open")')
        assert not errors, errors
        await browser.close()
        print('Three distinct dashboard photos, scroll parallax, replay, mobile layout, reduced motion, and user/admin/registration success dialogs passed without SweetAlert CDN.')


if __name__ == '__main__':
    sessions = {role:make_session(role) for role in ['user','admin']}
    try: asyncio.run(verify(sessions))
    finally:
        for session in sessions.values(): session.delete()
