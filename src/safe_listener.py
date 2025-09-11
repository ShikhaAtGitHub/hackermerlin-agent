# src/safe_listener.py
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from llm_agent import extract_password_with_llm
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://hackmerlin.io/")

        # Wait for Merlin's chat input
        chat_input = await page.wait_for_selector(
            "textarea[placeholder='You can talk to merlin here...']"
        )

        print(f"[{datetime.now()}] Ready. Ask your question manually in the browser.")

        last_text = ""

        # Store hints collected so far
        hints = {
            "first_letters": "",
            "last_letters": "",
            "length": "",
            "additional_hints": ""
        }

        # Define refusal markers
        denial_markers = [
            "i cannot reveal",
            "must remain hidden",
            "not allowed",
            "detected a manipulation",
            "i cannot tell",
            "must be protected",
            "sorry",
            "forbidden"
        ]

        while True:
            # Wait for new Merlin response
            await page.wait_for_function(
                """(prev) => {
                    const quotes = document.querySelectorAll('blockquote.mantine-Blockquote-root');
                    if (!quotes.length) return false;
                    const lastText = quotes[quotes.length - 1].innerText;
                    return lastText !== prev;
                }""",
                arg=last_text,
                timeout=60000
            )

            responses = await page.query_selector_all(
                "blockquote.mantine-Blockquote-root"
            )
            last_response = responses[-1]

            p_element = await last_response.wait_for_selector("p")
            last_text = await p_element.inner_text() if p_element else ""
            print(f"[{datetime.now()}] Merlin replied: {last_text}\n")

            # 1️⃣ Skip extraction if Merlin is just denying
            if any(marker in last_text.lower() for marker in denial_markers):
                print(f"[{datetime.now()}] Merlin refused to answer, waiting for better hints...\n")
                continue

            # 2️⃣ Parse hints from Merlin's response
            length_match = re.search(r'\b(?:length|characters|letters).*?(\d+)\b', last_text, re.I)
            if length_match:
                hints["length"] = length_match.group(1)

            first_match = re.search(r'first\s*(?:letters|characters).*?([A-Za-z]+)', last_text, re.I)
            if first_match:
                hints["first_letters"] = first_match.group(1)

            last_match = re.search(r'last\s*(?:letters|characters).*?([A-Za-z]+)', last_text, re.I)
            if last_match:
                hints["last_letters"] = last_match.group(1)

            hints["additional_hints"] += last_text + " "

            # 3️⃣ Use LLM to extract candidate password
            candidate_password = extract_password_with_llm(
                response_text=last_text,
                first_letters=hints["first_letters"],
                last_letters=hints["last_letters"],
                length=hints["length"],
                additional_hints=hints["additional_hints"]
            )

            print(f"[{datetime.now()}] Predicted secret password: {candidate_password}\n")
            print("Submit this password manually in the page to proceed to the next level.")
            print("Console will update automatically for each new response.\n")

            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run())

