import asyncio
from src.playwright_interface import start_browser, close_browser
from src.safe_listener import run
from src.hint_accumulator import HintAccumulator

async def main():
    browser, page = await start_browser(headless=False)
    await page.goto("https://hackmerlin.io/")

    hint_acc = HintAccumulator()
    tried = set()
    question_context = {}

    try:
        await run(hint_acc, question_context, tried, page, start_level=1)
    finally:
        await close_browser(browser)

if __name__ == "__main__":
    asyncio.run(main())
