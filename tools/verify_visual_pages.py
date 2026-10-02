"""Read-only browser checks of the real routes; screenshots stay in output/ui."""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.runtime'))
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
import django
django.setup()
from django.contrib.sessions.backends.db import SessionStore
from register.models import Register
from playwright.async_api import async_playwright


def make_session(role='user', pending=False):
    user = Register.objects.exclude(status='hibernated').first()
    store = SessionStore()
    store['u_id'] = user.register_id if user else 1
    store['type'] = role
    if pending and user:
        store['pending_financial_msg'] = 'UI verification only'
        store['pending_financial_receiver'] = 999999
        store['financial_email_notice'] = 'Email delivery has not been configured. Ask the administrator to complete Gmail setup.'
    store.save()
    return store


async def main(sessions):
    output = ROOT / 'output/ui'
    output.mkdir(parents=True, exist_ok=True)
    report = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            for mobile in [False, True]:
                for role, paths in {
                    'public': ['/', '/login/login/', '/register/register/'],
                    'user': ['/index/index3/', '/index/index1/', '/index/index4/', '/index/explore/', '/register/profile/', '/image/image/', '/image/add_story/', '/login/messages/', '/login/financial_otp_verify/', '/complaint/complaint/', '/complaint/view_replies/', '/feedback/feedback/'],
                    'admin': ['/index/index2/', '/register/individual-user/', '/register/admin_view/', '/image/view/', '/complaint/view/', '/feedback/view/'],
                }.items():
                    context = await browser.new_context(viewport={'width':390 if mobile else 1440, 'height':844 if mobile else 1000}, reduced_motion='reduce')
                    if role != 'public':
                        await context.add_cookies([{'name':'sessionid','value':sessions[role].session_key,'domain':'127.0.0.1','path':'/'}])
                    page = await context.new_page()
                    for index, path in enumerate(paths):
                        errors = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        response = await page.goto('http://127.0.0.1:8010' + path, wait_until='domcontentloaded')
                        await page.wait_for_timeout(900)
                        data = await page.evaluate('''() => ({
                            sharedStyle: !!document.querySelector('link[href*="visual-experience"]'),
                            logo: !!document.querySelector('img[src*="assenttag-logo.png"]'),
                            logoLoaded: Array.from(document.querySelectorAll('img[src*="assenttag-logo.png"]')).every(i => i.complete && i.naturalWidth > 0),
                            overflow: document.documentElement.scrollWidth > innerWidth + 2,
                            animated: document.querySelectorAll('.at-revealed').length,
                            background: getComputedStyle(document.body).backgroundImage,
                            pagePhoto: document.body.dataset.atPhoto || getComputedStyle(document.body).getPropertyValue('--at-art').trim(),
                            photosLoaded: Array.from(document.querySelectorAll('.at-page-photo img,.at-dashboard-welcome img,.at-otp-photo img,.at-explore-photo img')).every(i => i.complete && i.naturalWidth > 0),
                        })''')
                        report.append({'role':role,'mobile':mobile,'path':path,'status':response.status,**data,'errors':errors})
                        if path in ['/', '/login/login/', '/register/register/', '/index/index3/', '/login/financial_otp_verify/', '/index/index2/', '/index/index4/', '/image/image/', '/register/profile/', '/login/messages/']:
                            name = {'/':'index','/login/login/':'login','/register/register/':'register','/index/index3/':'dashboard','/login/financial_otp_verify/':'otp','/index/index2/':'admin','/index/index4/':'notifications','/image/image/':'upload','/register/profile/':'profile','/login/messages/':'comms'}[path]
                            if path == '/':
                                for chapter in await page.locator('.at-workflow-chapter').all():
                                    await chapter.scroll_into_view_if_needed()
                                    await chapter.locator('img').evaluate('(img) => img.decode()')
                                assert await page.locator('.at-workflow-chapter').count() == 8
                                assert await page.locator('.at-workflow-photo img').evaluate_all('(images) => new Set(images.map(i => i.src)).size === 8 && images.every(i => i.complete && i.naturalWidth > 0)')
                                await page.evaluate('scrollTo(0,0)')
                            await page.screenshot(path=str(output / f'{name}-{"mobile" if mobile else "desktop"}.png'), full_page=True)
                    await context.close()
            await browser.close()
    finally:
        pass
    (output / 'browser-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    failures = [item for item in report if item['status'] != 200 or not item['sharedStyle'] or not item['logoLoaded'] or not item['logo'] or not item['photosLoaded'] or item['errors'] or item['overflow']]
    desktop = [item for item in report if not item['mobile']]
    assert len({item['pagePhoto'] for item in desktop}) == len(desktop), 'Primary pages must have distinct photographic scenes'
    print(json.dumps({'checked':len(report),'failures':failures}, indent=2))
    assert not failures, 'Visual page verification failed'


async def verify_interactions():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width':1440, 'height':1000})
        await page.goto('http://127.0.0.1:8010/', wait_until='domcontentloaded')
        await page.wait_for_timeout(1600)
        await page.screenshot(path=str(ROOT / 'output/ui/index-animated.png'))
        await page.locator('.at-workflow-chapter').last.scroll_into_view_if_needed()
        await page.wait_for_timeout(1000)
        assert await page.locator('.at-workflow-chapter.at-revealed').count() >= 1
        assert await page.locator('.at-word').count() > 0
        assert await page.locator('.at-scene-layer.is-active').evaluate('(el) => el.style.backgroundImage.includes("photo-consent.webp")')
        await page.screenshot(path=str(ROOT / 'output/ui/consent-animated.png'))
        assert not await page.locator('h1').evaluate('(el) => el.classList.contains("at-text-visible")')
        await page.evaluate('scrollTo({top:0,behavior:"instant"})')
        await page.wait_for_timeout(1000)
        assert await page.locator('h1').evaluate('(el) => el.classList.contains("at-text-visible")')
        hero = await page.locator('.hero-graphic').bounding_box()
        assert abs(hero['x'] + hero['width'] / 2 - 720) < 3, 'Landing image must remain centered'
        assert await page.locator('h1').evaluate('(el) => getComputedStyle(el).animationName.includes("at-text-flow")')
        await page.locator('.toggle-btn').click()
        await page.wait_for_timeout(400)
        assert await page.locator('body').evaluate('(el) => el.classList.contains("light-mode")')
        await page.wait_for_function('getComputedStyle(document.body).color === "rgb(23, 35, 60)"')
        await page.locator('.toggle-btn').click()
        assert not await page.locator('body').evaluate('(el) => el.classList.contains("light-mode")')
        await page.goto('http://127.0.0.1:8010/login/login/', wait_until='domcontentloaded')
        await page.wait_for_timeout(1600)
        await page.screenshot(path=str(ROOT / 'output/ui/login-animated.png'))
        await page.set_viewport_size({'width':390, 'height':844})
        for path, name in [('/', 'index'), ('/login/login/', 'login'), ('/register/register/', 'register')]:
            await page.goto('http://127.0.0.1:8010' + path, wait_until='domcontentloaded')
            await page.wait_for_timeout(1600)
            assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth + 2'), name
            await page.screenshot(path=str(ROOT / f'output/ui/{name}-mobile-animated.png'), full_page=True)
        print('Workflow photo changes, word reveals, animated text, and existing light/dark toggle passed.')
        await browser.close()


async def verify_dashboard_and_otp(session):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width':1440,'height':1000})
        await context.add_cookies([{'name':'sessionid','value':session.session_key,'domain':'127.0.0.1','path':'/'}])
        page = await context.new_page()
        await page.goto('http://127.0.0.1:8010/index/index3/')
        await page.wait_for_timeout(1600)
        assert await page.locator('.at-compose-submit').is_visible()
        assert await page.locator('.at-compose-submit').get_attribute('type') == 'submit'
        assert await page.locator('nav .pill-btn').first.evaluate('(el) => getComputedStyle(el).borderTopRightRadius === "7px"')
        await page.screenshot(path=str(ROOT / 'output/ui/dashboard-new-animated.png'))
        await page.locator('.at-dashboard-pathways').scroll_into_view_if_needed()
        await page.wait_for_timeout(1500)
        assert await page.locator('.post-card.at-revealed').count() > 0
        assert await page.locator('.at-scene-layer.is-active').evaluate('(el) => !el.style.backgroundImage.includes("photo-dashboard.webp")')
        assert await page.locator('.at-pathway img').evaluate_all('(images) => images.length === 2 && images.every(i => i.complete && i.naturalWidth > 0)')
        for path in ['/index/index4/','/image/image/','/register/profile/','/index/index1/']:
            await page.goto('http://127.0.0.1:8010/index/index3/')
            await page.locator(f'nav a[href="{path}"]').click()
            assert page.url.endswith(path), path
        for path in ['/index/explore/','/login/messages/','/register/profile/']:
            await page.goto('http://127.0.0.1:8010/index/index3/')
            await page.locator(f'.shortcut-item[href="{path}"]').click()
            assert page.url.endswith(path), path
        await page.set_viewport_size({'width':390,'height':844})
        await page.goto('http://127.0.0.1:8010/index/index3/')
        await page.wait_for_timeout(1400)
        assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
        assert await page.locator('.right-column .profile-card').is_visible()
        assert await page.locator('.at-suggestions-panel').is_visible()
        assert await page.locator('.at-trending-panel').is_visible()
        await page.screenshot(path=str(ROOT / 'output/ui/dashboard-new-mobile.png'), full_page=True)
        # Isolated presentation fixture; no email or real chat message is sent.
        from login.otp import binding, CHALLENGE_KEY
        def countdown_fixture():
            user = Register.objects.get(register_id=session['u_id'])
            now = int(time.time())
            session[CHALLENGE_KEY] = {'expires':now+5,'binding':binding(session,user),'attempts':0,'nonce':'ui-only','digest':'ui-only'}
            session['financial_email_rate'] = {'last':now-55,'start':now,'count':1}
            session.save()
        await asyncio.to_thread(countdown_fixture)
        await page.goto('http://127.0.0.1:8010/login/financial_otp_verify/')
        assert await page.locator('#otp-verify').is_enabled()
        assert await page.locator('#otp-resend').is_disabled()
        await page.wait_for_timeout(6000)
        assert await page.locator('#otp-verify').is_disabled()
        assert await page.locator('#email-otp').is_disabled()
        assert await page.locator('#otp-resend').is_enabled()
        assert 'expired' in (await page.locator('#otp-countdown').inner_text()).lower()
        await page.reload()
        await page.wait_for_timeout(1400)
        assert await page.locator('#otp-verify').is_disabled()
        assert await page.locator('#otp-resend').is_enabled()
        await page.screenshot(path=str(ROOT / 'output/ui/otp-expired-mobile.png'), full_page=True)
        print('Dashboard navigation, photo transitions, mobile layout, and OTP expiry/resend UI passed.')
        await browser.close()


if __name__ == '__main__':
    if '--dashboard' in sys.argv:
        session = make_session('user', pending=True)
        try: asyncio.run(verify_dashboard_and_otp(session))
        finally: session.delete()
        sys.exit(0)
    if '--interactions' in sys.argv:
        asyncio.run(verify_interactions())
        sys.exit(0)
    sessions = {role: make_session(role, pending=role == 'user') for role in ['user', 'admin']}
    try:
        asyncio.run(main(sessions))
    finally:
        for session in sessions.values(): session.delete()
