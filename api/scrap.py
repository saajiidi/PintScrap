# api/scrape.py
import os
import requests
from playwright.sync_api import sync_playwright

def download_image(url):
    """Download image and return its content."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def scrape_pinterest(query, num_images=5):
    """Scrape Pinterest for images using Playwright."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.pinterest.com/search/pins/?q={query}", wait_until="domcontentloaded")
        
        # Wait for images to load
        page.wait_for_timeout(2000)
        
        # Scroll once to load more images
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        
        # Find images
        images = page.query_selector_all("img")
        for i, img in enumerate(images[:num_images]):
            img_url = img.get_attribute("src")
            if img_url and img_url.startswith("http"):
                img_data = download_image(img_url)
                if img_data:
                    results.append({"url": img_url, "index": i + 1})
        
        browser.close()
    return results

def handler(request):
    """Vercel serverless function handler."""
    try:
        query = request.args.get("query", "default")
        num = int(request.args.get("num", "5"))
        if num > 10:  # Limit for serverless timeout
            num = 10
        
        images = scrape_pinterest(query, num)
        return {
            "statusCode": 200,
            "body": str({"message": f"Scraped {len(images)} images", "images": images}),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }