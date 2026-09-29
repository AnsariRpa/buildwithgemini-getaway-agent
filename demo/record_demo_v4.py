import os
import time
from playwright.sync_api import sync_playwright

OUT_DIR = "/config/Desktop/BuildWithGemini/demo/v4_record"
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
    print("Navigating to frontend...")
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero", timeout=15000)
    time.sleep(3.0)

    # 2. First prompt: Quick getaway curation chip ("Under 2 hrs drive")
    print("Clicking prompt 1 chip...")
    chip = page.locator("button.chip-btn", has_text="Under 2 hrs drive")
    chip.click()
    page.wait_for_selector(".a2card", timeout=45000)
    # Wait for typing indicator to disappear
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=45000)
    print("Prompt 1 done.")
    time.sleep(4.5)

    # 3. Second prompt: Richer prompt with image generation + budget calculation tool
    print("Typing prompt 2...")
    input_box = page.locator("#input")
    input_box.click()
    prompt_text = "Generate a scenic travel postcard image for Lake Tahoe and calculate a $500 weekend budget breakdown"
    input_box.type(prompt_text, delay=25)
    time.sleep(0.8)
    page.locator("button.send-btn").click()

    # Wait for second response:
    print("Waiting for prompt 2 card and image...")
    # First wait for the image element to exist
    page.wait_for_selector("img.a2img", timeout=90000)
    # Wait until image is completely loaded
    page.wait_for_function("() => { const img = document.querySelector('img.a2img'); return img && img.complete && img.naturalWidth > 0; }", timeout=45000)
    # Wait until typing indicator finishes
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=30000)
    print("Card 2 & image fully loaded!")

    # Scroll down smoothly to show the postcard image and budget calculation
    time.sleep(2.0)
    for _ in range(5):
        page.evaluate("document.getElementById('log').scrollBy({top: 260, behavior: 'smooth'});")
        time.sleep(1.2)
    time.sleep(8.0)  # Generous time to showcase postcard and budget breakdown

    print("Closing browser...")
    page.close()
    context.close()
    browser.close()

files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_V4_SUCCESS=" + files[0])
