import os
import time
from playwright.sync_api import sync_playwright

VIDEO_DIR = "/config/Desktop/BuildWithGemini/demo/raw_video"
# Clean previous recordings
for f in os.listdir(VIDEO_DIR):
    if f.endswith(".webm"):
        os.remove(os.path.join(VIDEO_DIR, f))

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--window-size=1280,800", "--disable-gpu"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        record_video_dir=VIDEO_DIR,
        record_video_size={"width": 1280, "height": 800}
    )
    page = context.new_page()

    # 1. Open Getaway Concierge frontend
    page.goto("http://localhost:8080")
    page.wait_for_selector("#welcomeHero", timeout=15000)
    time.sleep(3.0)  # Showcase welcome card, title, and quick trip filters

    # 2. First prompt: Quick getaway curation ("Under 2 hrs drive")
    chip = page.locator("button.chip-btn", has_text="Under 2 hrs drive")
    chip.click()

    # Wait for the agent's first reply card to complete rendering (wait for text to appear inside .a2card)
    page.wait_for_selector(".a2card", timeout=60000)
    time.sleep(5.0)  # Let viewer read the curated getaways (Sonoma, Half Moon Bay, Napa Valley)

    # 3. Second richer prompt: Scenic travel postcard image + budget calculation
    chat_input = page.locator("#input")
    chat_input.click()
    prompt_text = "Generate a scenic travel postcard image for Lake Tahoe and calculate a $500 weekend budget breakdown"
    chat_input.type(prompt_text, delay=35)
    time.sleep(1.0)
    page.locator("button.send-btn").click()

    # Wait for second card to arrive and specifically wait for the postcard image element to render and load
    page.wait_for_selector(".a2card .a2img", timeout=75000)
    time.sleep(2.0)
    
    # Smooth scroll to show the full postcard image and budget breakdown
    page.evaluate("document.getElementById('log').scrollBy({top: 800, behavior: 'smooth'});")
    time.sleep(7.0)  # Generous time to showcase image and budget calculation card

    context.close()
    browser.close()

files = [os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR) if f.endswith(".webm")]
if files:
    print("RECORDING_SUCCESS=" + files[0])
