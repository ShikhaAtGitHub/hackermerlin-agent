# src/main_with_llm.py
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from llm_agent import extract_password_with_llm

async def run():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://hackmerlin.io/")

        # Wait for Merlin's chat input
        chat_input = await page.wait_for_selector(
            "textarea[placeholder='You can talk to merlin here...']"
        )

        print(f"[{datetime.now()}] Ready. Ask your question manually in the browser.")

        # Keep track of last blockquote text to detect updates
        last_text = ""

        while True:
            # Wait until the last blockquote text changes
            await page.wait_for_function(
                """(prev) => {
                    const quotes = document.querySelectorAll('blockquote.mantine-Blockquote-root');
                    if (!quotes.length) return false;
                    const lastText = quotes[quotes.length - 1].innerText;
                    return lastText !== prev;
                }""",
                arg=last_text,
                timeout=60000  # wait up to 60 seconds
            )

            # Get the updated last blockquote
            responses = await page.query_selector_all(
                "blockquote.mantine-Blockquote-root"
            )
            last_response = responses[-1]

            # Wait for the <p> inside the last blockquote to appear
            p_element = await last_response.wait_for_selector("p")
            last_text = await p_element.inner_text() if p_element else ""
            print(f"[{datetime.now()}] Merlin replied: {last_text}\n")

            # Use LLM to extract candidate password
            candidate_password = extract_password_with_llm(last_text)
            print(f"[{datetime.now()}] Predicted secret password: {candidate_password}\n")

            print(
                "Submit this password manually in the page to proceed to the next level."
            )
            print("Console will update automatically for each new response.\n")

            # Small delay before checking again
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run())

