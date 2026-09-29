import os
import time
from playwright.sync_api import sync_playwright

OUT_DIR = "/config/Desktop/BuildWithGemini/demo/v10_record"
os.makedirs(OUT_DIR, exist_ok=True)
for f in os.listdir(OUT_DIR):
    if f.endswith(".webm"):
        os.remove(os.path.join(OUT_DIR, f))

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--window-size=1280,800", "--disable-gpu"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        record_video_dir=OUT_DIR,
        record_video_size={"width": 1280, "height": 800}
    )
    page = context.new_page()

    # Step 1: Land on homepage with welcome hero & quick prompt chips
    print("Navigating...")
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero", timeout=15000)
    time.sleep(3.0)

    # Step 2: Prompt 1 - Click quick chip "Under 2 hrs drive"
    print("Clicking prompt 1 chip...")
    chip = page.locator("button.chip-btn", has_text="Under 2 hrs drive")
    chip.click()
    page.wait_for_selector(".a2card", timeout=45000)
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=45000)
    print("Prompt 1 finished!")
    time.sleep(4.0)

    # Step 3: Prompt 2 - Click the rich prompt chip "Lake Tahoe Adventure & Budget"
    print("Clicking prompt 2 chip...")
    tahoe_chip = page.locator("button.chip-btn", has_text="Lake Tahoe Adventure & Budget")
    tahoe_chip.click()

    # Wait for the second card with image to appear and finish loading
    print("Waiting for prompt 2 image card...")
    page.wait_for_selector("img.a2img", timeout=120000)
    print("img.a2img found! Waiting for naturalWidth > 0...")
    page.wait_for_function("() => { const img = document.querySelector('img.a2img'); return img && img.complete && img.naturalWidth > 0; }", timeout=30000)
    print("Postcard image loaded! Waiting for stream to finish...")
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=30000)
    time.sleep(2.0)

    # Step 4: Smooth scroll down to highlight the generated postcard image and budget calculation
    print("Smooth scrolling...")
    for _ in range(6):
        page.evaluate("document.getElementById('log').scrollBy({top: 250, behavior: 'smooth'});")
        time.sleep(1.2)
    time.sleep(7.0)

    print("Closing browser...")
    page.close()
    context.close()
    browser.close()

files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_V10_SUCCESS=" + files[0])
