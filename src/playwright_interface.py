# src/playwright_interface.py
"""
Playwright helpers for HackerMerlin automation.

Functions:
 - start_browser(headless=False) -> (browser, page)
 - get_challenge_text(page) -> str
 - get_latest_merlin_response(page) -> str
 - send_message(page, text) -> None
 - submit_password(page, candidate, submit_with_enter=True, timeout=3) -> bool
 - wait_for_new_response(page, prev_text, timeout=30) -> (new_text or None)
 - close_browser(browser) -> None

Notes:
 - This module tries to be robust to minor DOM timing quirks by using wait_for_selector / wait_for_function.
 - Detection of submit success/failure is heuristic: we check for an obvious failure message (user observed
   "Bad secret word" / "This isn't the secret phrase..." in the UI). If no failure message appears and the
   last response text changes, we treat it as success. Adjust heuristics as needed.
"""

import asyncio
from typing import Optional, Tuple
from playwright.async_api import Browser, Page, async_playwright, TimeoutError as PWTimeout
from datetime import datetime


# --------- Low-level helpers ---------
async def start_browser(headless: bool = False, slow_mo: int = 0) -> Tuple[Browser, Page]:
    pw = await async_playwright().__aenter__()  # caller is responsible for closing browser via close_browser
    browser = await pw.chromium.launch(headless=headless, slow_mo=slow_mo)
    page = await browser.new_page()
    return browser, page


async def close_browser(browser: Browser):
    try:
        await browser.close()
    except Exception:
        pass
    # playwright context cleanup is left to process exit in this helper-based approach


# --------- Page interactions ---------
async def get_challenge_text(page: Page, timeout: int = 10) -> str:
    """
    Read the main challenge / instruction text from the page.
    Returns empty string if not found.
    """
    # Possible challenge locations include Mantine Text-root elements near the top.
    try:
        el = await page.wait_for_selector("div.mantine-Text-root", timeout=timeout * 1000)
        text = (await el.inner_text()).strip()
        return text
    except PWTimeout:
        return ""


async def get_latest_merlin_response(page: Page, timeout: int = 10) -> str:
    """
    Return the textual content of the last Merlin response (<p> inside the last blockquote).
    Returns empty string if not found within timeout.
    """
    try:
        # Wait for at least one blockquote to exist
        await page.wait_for_selector("blockquote.mantine-Blockquote-root", timeout=timeout * 1000)
        responses = await page.query_selector_all("blockquote.mantine-Blockquote-root")
        last = responses[-1]
        # Wait for the <p> to be attached inside the last blockquote (handles dynamic insertion)
        p_el = await last.wait_for_selector("p", timeout=timeout * 1000)
        text = (await p_el.inner_text()).strip()
        return text
    except PWTimeout:
        # fallback: try to read whole blockquote text and strip cite if present
        try:
            responses = await page.query_selector_all("blockquote.mantine-Blockquote-root")
            if not responses:
                return ""
            raw = await responses[-1].inner_text()
            # remove signature if present
            cleaned = raw.split("– Merlin")[0].strip()
            return cleaned
        except Exception:
            return ""
    except Exception:
        return ""


async def wait_for_new_response(page: Page, prev_text: str, timeout: int = 30) -> Optional[str]:
    """
    Wait up to timeout seconds for the last blockquote innerText to change from prev_text.
    Returns the new last response text (cleaned) or None on timeout.
    """
    try:
        await page.wait_for_function(
            """(prev) => {
                const quotes = document.querySelectorAll('blockquote.mantine-Blockquote-root');
                if (!quotes.length) return false;
                const lastText = quotes[quotes.length - 1].innerText;
                return lastText !== prev;
            }""",
            arg=prev_text,
            timeout=timeout * 1000,
        )
    except PWTimeout:
        return None

    # once changed, fetch the latest response (use the robust getter)
    return await get_latest_merlin_response(page, timeout=5)


async def send_message(page: Page, text: str, press_enter: bool = True) -> None:
    """
    Fill the chat input and optionally press Enter.
    """
    input_sel = "textarea[placeholder='You can talk to merlin here...']"
    el = await page.wait_for_selector(input_sel, timeout=10 * 1000)
    await el.fill(text)
    if press_enter:
        await el.press("Enter")
    # small pause to let UI react
    await asyncio.sleep(0.2)


async def submit_password(page: Page, candidate: str, submit_with_enter: bool = True, timeout: int = 5) -> bool:
    """
    Fill password input and submit; return True if submission appears to succeed, False if a known failure appears.
    Heuristics:
      - After submission, check for an element containing 'Bad secret' or similar (failure).
      - If no failure message is detected and the last blockquote or challenge changes soon after, assume success.
    """
    # Fill password
    pw_sel = "input[placeholder='SECRET PASSWORD']"
    el = await page.wait_for_selector(pw_sel, timeout=10 * 1000)
    # Make sure candidate is a string
    candidate = "" if candidate is None else str(candidate)
    await el.fill(candidate)
    if submit_with_enter:
        await el.press("Enter")
    else:
        # try to click a submit button if exists (safe fallback)
        try:
            btn = await page.query_selector("button:has-text('Submit')")
            if btn:
                await btn.click()
        except Exception:
            pass

    # small wait for UI to respond
    await asyncio.sleep(0.5)

    # Check for a failure message (common string observed: "Bad secret word" or "This isn't the secret phrase")
    try:
        # look for an element containing failure text (case-insensitive)
        failure = await page.query_selector("text=/Bad secret/i")
        if not failure:
            # also check the longer phrase fragment if present
            failure = await page.query_selector("text=/secret phrase/i")
        if failure:
            # found a failure message: consider it a failed submission
            return False
    except Exception:
        pass

    # If no explicit failure detected, assume success if challenge or last response changes within timeout
    # capture pre state
    try:
        prev_text = await get_latest_merlin_response(page, timeout=2)
    except Exception:
        prev_text = ""

    # wait a short while for new UI (either success modal or next level challenge to appear)
    new_text = await wait_for_new_response(page, prev_text, timeout=timeout)
    if new_text is not None and new_text != prev_text:
        # the page updated and produced a new Merlin response => likely progressed
        return True

    # no update and no explicit failure observed -> assume failure for safety
    return False
