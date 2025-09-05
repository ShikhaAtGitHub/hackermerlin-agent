# src/main.py
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/tmp/playwright",  # stores session data
            headless=False
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://hackmerlin.io/")
        print("Page title:", await page.title())

        # no auto-close: stays open until we stop script
        await asyncio.sleep(9999)

if __name__ == "__main__":
    asyncio.run(run())