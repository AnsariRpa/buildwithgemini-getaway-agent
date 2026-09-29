import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero")
    
    # Click prompt 1
    print("Clicking prompt 1...")
    page.locator("button.chip-btn", has_text="Under 2 hrs drive").click()
    page.wait_for_selector(".a2card", timeout=45000)
    page.wait_for_function("() => !document.querySelector('.typing-indicator')")
    print("Prompt 1 done. Rows count:", page.evaluate("document.querySelectorAll('.msg-row').length"))

    # Click prompt 2
    print("Clicking prompt 2...")
    page.locator("button.chip-btn", has_text="Lake Tahoe Adventure & Budget").click()
    print("Prompt 2 clicked. Waiting 25s...")
    
    for i in range(25):
        time.sleep(1.0)
        typing = page.evaluate("!!document.querySelector('.typing-indicator')")
        rows = page.evaluate("document.querySelectorAll('.msg-row').length")
        cards = page.evaluate("document.querySelectorAll('.a2card').length")
        imgs = page.evaluate("document.querySelectorAll('img.a2img').length")
        print(f"[{i}s] typing={typing}, rows={rows}, cards={cards}, imgs={imgs}")
        if not typing and cards >= 2:
            print("Both cards rendered!")
            break

    page.screenshot(path="/config/Desktop/BuildWithGemini/demo/debug_two_prompts.jpg")
    browser.close()
