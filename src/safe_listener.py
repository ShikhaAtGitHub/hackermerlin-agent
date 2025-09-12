# src/safe_listener.py
import asyncio
import re
from datetime import datetime
from src.llm_agent import extract_password_with_llm
from src.hint_accumulator import HintAccumulator


async def run(hint_acc: HintAccumulator, question_context: dict, tried: set, page):
    """Listen to Merlin's responses on an already opened page and try passwords."""
    await page.wait_for_selector("textarea[placeholder='You can talk to merlin here...']")
    print(f"[{datetime.now()}] ✅ Ready. Ask your question manually in the browser.")

    last_text = ""

    denial_markers = [
        "i cannot reveal", "must remain hidden", "not allowed",
        "detected a manipulation", "i cannot tell", "must be protected",
        "sorry", "forbidden"
    ]

    while True:
        # Wait for a new Merlin response
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

        responses = await page.query_selector_all("blockquote.mantine-Blockquote-root")
        last_response = responses[-1]
        p_element = await last_response.wait_for_selector("p")
        last_text = await p_element.inner_text() if p_element else ""

        print(f"[{datetime.now()}] Merlin replied: {last_text}\n")

        # Record Q/A if we know the last question
        if "last_question" in question_context:
            hint_acc.add_qa(question_context["last_question"], last_text)
            question_context.pop("last_question")

        # Skip denials
        if any(marker in last_text.lower() for marker in denial_markers):
            print(f"[{datetime.now()}] Merlin refused — waiting for better hints...\n")
            continue

        # Parse hints
        if m := re.search(r'\b(?:length|characters|letters).*?(\d+)\b', last_text, re.I):
            hint_acc.update("length", m.group(1))
        if m := re.search(r'first\s*(?:letters|characters).*?([A-Za-z]+)', last_text, re.I):
            hint_acc.update("first_letters", m.group(1))
        if m := re.search(r'last\s*(?:letters|characters).*?([A-Za-z]+)', last_text, re.I):
            hint_acc.update("last_letters", m.group(1))

        hint_acc.update("additional_hints", last_text)

        # Collect uppercase tokens
        tokens = re.findall(r'\b[A-Z]{3,}\b', last_text)
        for token in tokens:
            hint_acc.update("tokens", token)

        # Track question context
        if "reverse" in last_text.lower():
            question_context["reverse"] = True
        if "descending" in last_text.lower():
            question_context["reverse"] = True

        # Candidate synthesis
        candidate_password = None
        for token in hint_acc.get("tokens"):
            if hint_acc.get("length") and len(token) != int(hint_acc.get("length")):
                continue
            if hint_acc.get("first_letters") and not token.startswith(hint_acc.get("first_letters")):
                continue
            if hint_acc.get("last_letters") and not token.endswith(hint_acc.get("last_letters")):
                continue
            candidate_password = token
            break

        if not candidate_password:
            candidate_password = extract_password_with_llm(
                response_text=last_text,
                first_letters=hint_acc.get("first_letters"),
                last_letters=hint_acc.get("last_letters"),
                length=hint_acc.get("length"),
                additional_hints=hint_acc.get("additional_hints"),
                question_context=question_context,
                qa_pairs=hint_acc.get("qa_pairs"),
                tokens=hint_acc.get("tokens"),
            )

        if not candidate_password or candidate_password in tried:
            continue

        tried.add(candidate_password)
        print(f"[{datetime.now()}] 🔑 Predicted password: {candidate_password}\n")

        # Auto-submit
        try:
            pw_selector = "input[placeholder='SECRET PASSWORD']"
            await page.fill(pw_selector, candidate_password)
            await page.click("button:has-text('Submit')")
            await asyncio.sleep(2)

            popup = await page.query_selector("div[role='dialog'], div[class*='mantine-Modal']")
            if popup:
                popup_text = await popup.inner_text()
                if "Awesome job!" in popup_text:
                    print(f"[{datetime.now()}] 🎉 SUCCESS with: {candidate_password}")
                    hint_acc.clear()
                    tried.clear()
                    question_context.clear()
                elif "Bad secret" in popup_text or "isn't the secret phrase" in popup_text:
                    print(f"[{datetime.now()}] ❌ Failed with: {candidate_password}")
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ Error during submission: {e}")

        await asyncio.sleep(1)
