import asyncio
from typing import Optional, Tuple
from playwright.async_api import Browser, Page, async_playwright, TimeoutError as PWTimeout

# --------- Low-level helpers ---------
async def start_browser(headless: bool = False, slow_mo: int = 0) -> Tuple[Browser, Page]:
    pw = await async_playwright().__aenter__()
    browser = await pw.chromium.launch(headless=headless, slow_mo=slow_mo)
    page = await browser.new_page()
    return browser, page

async def close_browser(browser: Browser):
    try:
        await browser.close()
    except Exception:
        pass

# --------- Page interactions ---------
async def get_challenge_text(page: Page, timeout: int = 10) -> str:
    try:
        el = await page.wait_for_selector("div.mantine-Text-root", timeout=timeout * 1000)
        return (await el.inner_text()).strip()
    except PWTimeout:
        return ""

async def get_latest_merlin_response(page: Page, timeout: int = 10) -> str:
    try:
        await page.wait_for_selector("blockquote.mantine-Blockquote-root", timeout=timeout * 1000)
        responses = await page.query_selector_all("blockquote.mantine-Blockquote-root")
        last = responses[-1]
        p_el = await last.wait_for_selector("p", timeout=timeout * 1000)
        return (await p_el.inner_text()).strip()
    except PWTimeout:
        return ""
    except Exception:
        return ""

async def wait_for_new_response(page: Page, prev_text: str, timeout: int = 30) -> Optional[str]:
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
    return await get_latest_merlin_response(page, timeout=5)

async def send_message(page: Page, text: str, press_enter: bool = True) -> None:
    """
    Types the question and *also* clicks the Ask button (to avoid the intermittent 'no reply' issue).
    Retries once if no text change is detected.
    """
    input_sel = "textarea[placeholder='You can talk to merlin here...']"
    el = await page.wait_for_selector(input_sel, timeout=10 * 1000)
    prev = await get_latest_merlin_response(page, timeout=2)
    await el.fill(text)
    if press_enter:
        await el.press("Enter")

    # Explicitly click Ask button (robust to class changes)
    ask_selectors = [
        "button:has-text('Ask')",
        "button.mantine-Button-root",
        "button"
    ]
    for s in ask_selectors:
        try:
            btn = await page.query_selector(s)
            if btn:
                await btn.click()
                break
        except Exception:
            pass

    # small settle
    await asyncio.sleep(0.5)

    # retry once if nothing changed
    new_text = await get_latest_merlin_response(page, timeout=2)
    if new_text == prev:
        await el.fill(text)
        await el.press("Enter")
        for s in ask_selectors:
            try:
                btn = await page.query_selector(s)
                if btn:
                    await btn.click()
                    break
            except Exception:
                pass
        await asyncio.sleep(0.5)

async def submit_password(page: Page, candidate: str, submit_with_enter: bool = True, timeout: int = 5) -> bool:
    """
    Fill password input and submit; return True if submission appears to succeed, False if a known failure appears.
    """
    pw_sel_candidates = [
        "input[placeholder='SECRET PASSWORD']",
        "input[type='password']",
        "input.mantine-TextInput-input",
        "input[id^='mantine']",
        "input"
    ]
    pw_el = None
    for sel in pw_sel_candidates:
        pw_el = await page.query_selector(sel)
        if pw_el:
            pw_sel = sel
            break
    if not pw_el:
        return False

    candidate = "" if candidate is None else str(candidate)
    await pw_el.fill(candidate)

    if submit_with_enter:
        try:
            await pw_el.press("Enter")
        except Exception:
            pass

    # also try clicking submit
    for sel in ["button:has-text('Submit')", "button[type='submit']", "button"]:
        try:
            btn = await page.query_selector(sel)
            if btn:
                await btn.click()
                break
        except Exception:
            pass

    await asyncio.sleep(0.6)

    # explicit failure check
    try:
        failure = await page.query_selector("text=/Bad secret/i")
        if not failure:
            failure = await page.query_selector("text=/secret phrase/i")
        if failure:
            return False
    except Exception:
        pass

    # success if popup appears or last response changes
    popup = await page.query_selector("div[role='dialog'], div[class*='mantine-Modal']")
    if popup:
        return True

    prev_text = await get_latest_merlin_response(page, timeout=2)
    new_text = await wait_for_new_response(page, prev_text, timeout=timeout)
    return bool(new_text and new_text != prev_text)
