import os
import time
from playwright.sync_api import sync_playwright

OUT_DIR = "/config/Desktop/BuildWithGemini/demo/v8_record"
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

    # 1. Start on home screen
    print("Step 1: Land on page")
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero", timeout=15000)
    time.sleep(3.0)

    # 2. First prompt: Quick getaway curation chip ("Under 2 hrs drive")
    print("Step 2: Click prompt 1 chip")
    chip = page.locator("button.chip-btn", has_text="Under 2 hrs drive")
    chip.click()
    page.wait_for_selector(".a2card", timeout=45000)
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=45000)
    print("Prompt 1 done.")
    time.sleep(4.0)

    # 3. Second prompt: Richer prompt with image generation + budget calculation tool
    print("Step 3: Typing prompt 2...")
    input_box = page.locator("#input")
    input_box.click()
    prompt_text = "Generate a scenic travel postcard image for Lake Tahoe and calculate a $500 weekend budget breakdown"
    input_box.type(prompt_text, delay=25)
    time.sleep(0.8)
    page.locator("button.send-btn").click()

    # Wait for the second card with image to appear and finish loading
    print("Step 4: Waiting for prompt 2 image card...")
    # The image takes ~20s to generate
    page.wait_for_selector("img.a2img", timeout=120000)
    print("img.a2img element found! Waiting for image data to load...")
    page.wait_for_function("() => { const img = document.querySelector('img.a2img'); return img && img.complete && img.naturalWidth > 0; }", timeout=30000)
    print("Postcard image fully visible! Waiting for stream to finish...")
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=30000)
    time.sleep(2.0)

    # Smooth scroll down through the postcard image and budget table
    print("Step 5: Smooth scroll to showcase card")
    for _ in range(6):
        page.evaluate("document.getElementById('log').scrollBy({top: 250, behavior: 'smooth'});")
        time.sleep(1.2)
    time.sleep(7.0)

    print("Step 6: Closing browser...")
    page.close()
    context.close()
    browser.close()

files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_V8_SUCCESS=" + files[0])
