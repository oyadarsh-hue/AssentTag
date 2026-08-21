import asyncio
from playwright.async_api import async_playwright
import os

async def capture_trio():
    output_dir = r"C:\Users\HP\Downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # 1. Index (Homepage)
        print("Capturing Index...")
        await page.goto("http://localhost:8000/", wait_until="networkidle")
        await page.screenshot(path=os.path.join(output_dir, "1_index_page.png"))

        # 2. Login
        print("Capturing Login...")
        await page.goto("http://localhost:8000/login/login/", wait_until="networkidle")
        await page.screenshot(path=os.path.join(output_dir, "2_login_page.png"))

        # 3. Login to access Complaint (assuming it's protected)
        print("Logging in to capture Complaint...")
        await page.fill('input[name="email"]', "neo@matrix.com")
        await page.fill('input[name="password"]', "password")
        await page.select_option('select[name="role"]', "user")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)

        print("Capturing Complaint...")
        await page.goto("http://localhost:8000/complaint/complaint/", wait_until="networkidle")
        await page.screenshot(path=os.path.join(output_dir, "USER_Complaint_Page.png"))

        print("Done. Check Downloads folder.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_trio())
