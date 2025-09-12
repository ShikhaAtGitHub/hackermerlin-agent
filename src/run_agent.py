# src/run_agent.py
import asyncio
from src.playwright_interface import (
    start_browser,
    close_browser,
    get_challenge_text,
    send_message,
    submit_password,
    get_latest_merlin_response,
)
from src.safe_listener import run
from src.hint_accumulator import HintAccumulator


async def main():
    browser, page = await start_browser(headless=False)

    # Navigate to HackerMerlin website
    await page.goto("https://hackmerlin.io/")

    # Initialize shared state
    hint_acc = HintAccumulator()
    tried = set()
    question_context = {}

    print("⚡ Agent started. Type your questions in the browser input box.")

    try:
        # ✅ Instead of looping manually, just hand off to safe_listener once
        await run(hint_acc, question_context, tried, page)

    finally:
        await close_browser(browser)


# Example wrapper for asking programmatic questions
async def ask_merlin(page, text: str, question_context: dict):
    """Ask Merlin a question and store it in context for pairing with next reply."""
    await send_message(page, text)
    question_context["last_question"] = text


if __name__ == "__main__":
    asyncio.run(main())
