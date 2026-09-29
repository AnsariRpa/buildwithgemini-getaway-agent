import os
import time
from playwright.sync_api import sync_playwright

OUT_DIR = "/config/Desktop/BuildWithGemini/demo/v6_record"
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
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=45000)
    print("Prompt 1 done.")
    time.sleep(4.0)

    # 3. Second prompt: Richer prompt with image generation + budget calculation tool
    print("Typing prompt 2...")
    input_box = page.locator("#input")
    input_box.click()
    prompt_text = "Generate a scenic travel postcard image for Lake Tahoe and calculate a $500 weekend budget breakdown"
    input_box.type(prompt_text, delay=25)
    time.sleep(0.8)
    page.locator("button.send-btn").click()

    # Wait for the second card specifically
    print("Waiting for prompt 2 cards to finish streaming...")
    # Wait for typing indicator to show up then disappear
    time.sleep(2.0)
    page.wait_for_function("() => !document.querySelector('.typing-indicator')", timeout=75000)
    print("Typing indicator disappeared. Ensuring card 2 has rendered...")
    time.sleep(2.0)

    # Scroll down smoothly to show the second card completely
    print("Scrolling to reveal second card and budget...")
    for _ in range(6):
        page.evaluate("document.getElementById('log').scrollBy({top: 250, behavior: 'smooth'});")
        time.sleep(1.2)
    time.sleep(8.0)  # Generous linger time

    print("Closing browser...")
    page.close()
    context.close()
    browser.close()

files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_V6_SUCCESS=" + files[0])
