import os
import time
from playwright.sync_api import sync_playwright

OUT_DIR = "/config/Desktop/BuildWithGemini/demo/v3_record"
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
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero", timeout=15000)
    time.sleep(3.0)

    # 2. First prompt: Quick getaway curation chip ("Under 2 hrs drive")
    chip = page.locator("button.chip-btn", has_text="Under 2 hrs drive")
    chip.click()
    # Wait for the first A2UI card to fully render
    page.wait_for_selector(".a2card", timeout=45000)
    time.sleep(4.5)

    # 3. Second prompt: Richer prompt with image generation + budget calculation tool
    input_box = page.locator("#input")
    input_box.click()
    prompt_text = "Generate a scenic travel postcard image for Lake Tahoe and calculate a $500 weekend budget breakdown"
    input_box.type(prompt_text, delay=28)
    time.sleep(0.8)
    page.locator("button.send-btn").click()

    # Wait for the second card with img to appear and finish loading
    page.wait_for_selector(".a2card img.a2img", timeout=75000)
    page.wait_for_function("() => { const imgs = document.querySelectorAll('.a2card img.a2img'); return imgs.length > 0 && imgs[imgs.length-1].complete && imgs[imgs.length-1].naturalWidth > 0; }", timeout=30000)
    
    # Smooth scroll down to highlight the generated postcard image and budget calculation table
    time.sleep(2.0)
    for _ in range(4):
        page.evaluate("document.getElementById('log').scrollBy({top: 250, behavior: 'smooth'});")
        time.sleep(1.2)
    time.sleep(6.0)

    context.close()
    browser.close()

files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_V3=" + files[0])
