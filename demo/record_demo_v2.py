import os
import time
from playwright.sync_api import sync_playwright

OUT_DIR = "/config/Desktop/BuildWithGemini/demo/v2_record"
os.makedirs(OUT_DIR, exist_ok=True)
for f in os.listdir(OUT_DIR):
    if f.endswith(".webm"):
        os.remove(os.path.join(OUT_DIR, f))

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--window-size=1280,800", "--disable-gpu"]
    )
    # Using larger viewport
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        record_video_dir=OUT_DIR,
        record_video_size={"width": 1280, "height": 800}
    )
    page = context.new_page()

    # Step 1: Land on homepage with welcome hero & quick prompt chips
    print("Navigating to app...")
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero", timeout=15000)
    time.sleep(3.5)

    # Step 2: Trigger prompt 1 (instant weekend getaway curation)
    print("Clicking 'Under 2 hrs drive'...")
    chip = page.locator("button.chip-btn", has_text="Under 2 hrs drive")
    chip.click()
    
    # Wait for the agent response card to appear
    page.wait_for_selector(".a2card", timeout=45000)
    # Wait until typing indicator is gone and content is populated
    page.wait_for_function("() => !document.querySelector('.typing-indicator') && document.querySelectorAll('.a2card').length >= 1", timeout=45000)
    print("Prompt 1 complete.")
    time.sleep(4.5)

    # Step 3: Trigger prompt 2 (postcard image generation + budget calculation)
    print("Typing prompt 2...")
    input_box = page.locator("#input")
    input_box.click()
    prompt_text = "Generate a scenic travel postcard image for Lake Tahoe and calculate a $500 weekend budget breakdown"
    input_box.type(prompt_text, delay=30)
    time.sleep(1.0)
    page.locator("button.send-btn").click()

    # Wait for the second agent response: wait for the img element to appear and finish loading
    print("Waiting for prompt 2 with postcard image...")
    page.wait_for_selector(".a2card img.a2img", timeout=75000)
    page.wait_for_function("() => { const img = document.querySelector('.a2card img.a2img'); return img && img.complete && img.naturalWidth > 0; }", timeout=30000)
    print("Image loaded! Scrolling down to showcase full itinerary...")
    
    # Smooth scroll to show the full postcard and budget
    time.sleep(1.5)
    page.evaluate("document.getElementById('log').scrollTo({top: 9999, behavior: 'smooth'});")
    time.sleep(6.5)

    context.close()
    browser.close()

files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_SAVED=" + files[0])
