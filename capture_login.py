import asyncio
from playwright.async_api import async_playwright
import os

async def capture_login():
    output_dir = r"C:\Users\HP\Downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("Capturing Login Page...")
        await page.goto("http://localhost:8000/login/login/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        filepath = os.path.join(output_dir, "2_login_page.png")
        await page.screenshot(path=filepath, full_page=False)
        print(f"Captured Login Page: {filepath}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_login())
