# src/main.py
import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime

async def extract_password(text):
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text)
    if not words:
        return None

    # prefer lowercase
    for w in words:
        if w.islower():
            return w

    # fallback to last word
    return words[-1]

async def run():
    async with async_playwright() as p:
        # context = await p.chromium.launch_persistent_context(
        #     user_data_dir="/tmp/playwright",  # stores session data
        #     headless=False
        # )
        # page = context.pages[0] if context.pages else await context.new_page()
        # await page.goto("https://hackmerlin.io/")
        # print("Page title:", await page.title())

        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://hackmerlin.io/")

        # 1. locate chat input
        chat_input = await page.wait_for_selector("textarea[placeholder='You can talk to merlin here...']")

        # 2. ask Merlin a question
        question = "Who is the first President of the US?"
        await chat_input.fill(question)
        await chat_input.press("Enter")

        # 3. get all blockquote responses
        responses = await page.query_selector_all("blockquote.mantine-Blockquote-root")
        last_response = responses[-1] # pick the last one (most recent reply from Merlin)
        # extract only the <p> text, not the <cite>
        # wait for at least one blockquote
        await page.wait_for_selector("blockquote.mantine-Blockquote-root")

        # get all blockquotes
        responses = await page.query_selector_all("blockquote.mantine-Blockquote-root")
        last_response = responses[-1]
        # try to get the <p> text
        response_text_el = await last_response.query_selector("p")
        if response_text_el:
            response_text = await response_text_el.inner_text()
        else:
            # fallback: get all text and strip signature
            response_text = await last_response.inner_text()
            response_text = response_text.split("– Merlin")[0].strip()

        print("Merlin replied:", response_text)

        # 4: extract candidate password
        candidate = await extract_password(response_text)
        print(f"[{datetime.now()}] Candidate password: {candidate}")

        # 5. enter into password box
        password_input = await page.wait_for_selector("input[placeholder='SECRET PASSWORD']")
        await password_input.fill(candidate)
        await password_input.press("Enter")

        # no auto-close: stays open until we stop script
        await asyncio.sleep(9999)

if __name__ == "__main__":
    asyncio.run(run())