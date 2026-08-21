import asyncio
from playwright.async_api import async_playwright
import os

async def capture_edit_profile():
    output_dir = r"C:\Users\HP\Downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("Logging in to capture Edit Profile...")
        await page.goto("http://localhost:8000/login/login/")
        await page.fill('input[name="email"]', "neo@matrix.com")
        await page.fill('input[name="password"]', "password")
        await page.select_option('select[name="role"]', "user")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)

        # Using Neo's ID 2 (as found earlier)
        target_url = "http://localhost:8000/register/edit/2/"
        print(f"Navigating to {target_url}...")
        await page.goto(target_url, wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        filepath = os.path.join(output_dir, "USER_Edit_Profile_Page.png")
        await page.screenshot(path=filepath, full_page=False)
        print(f"Captured Profile Edit Page: {filepath}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_edit_profile())
