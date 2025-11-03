import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def _make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Do NOT use headless — Trade Me blocks it
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_trademe(query="teacher"):
    driver = _make_driver()
    url = f"https://www.trademe.co.nz/a/jobs/search?search_string={query}"
    driver.get(url)

    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Wait for category tiles or job cards
        wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, "div.tm-jobs-category-tile, div.tm-job-card"
            ))
        )

        # Step 2: If only category tiles show up (no job cards), click "Education" or first tile
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.tm-job-card")
        if not job_cards:
            print("🔍 Clicking category tile to reach job listings...")
            category_tiles = driver.find_elements(By.CSS_SELECTOR, "div.tm-jobs-category-tile")

            # Try to click "Education" tile if available
            clicked = False
            for tile in category_tiles:
                if "Education" in tile.text:
                    tile.click()
                    clicked = True
                    break

            # Fallback: click the first tile if "Education" not found
            if not clicked and category_tiles:
                category_tiles[0].click()

            time.sleep(2)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tm-job-card")))

        # Step 3: Scroll to load jobs
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Step 4: Scrape job cards
        jobs = []
        cards = driver.find_elements(By.CSS_SELECTOR, "div.tm-job-card")

        for card in cards:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a.tm-job-card__title")
                title = title_el.text.strip()
                link = title_el.get_attribute("href")
                company = card.find_element(By.CSS_SELECTOR, ".tm-job-card__company").text.strip()
                location = card.find_element(By.CSS_SELECTOR, ".tm-job-card__location").text.strip()
                posted = card.find_element(By.CSS_SELECTOR, ".tm-job-card__listing-date").text.strip()
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "posted": posted,
                    "link": link
                })
            except Exception:
                continue

        driver.quit()
        print(f"✅ Scraped {len(jobs)} jobs from Trade Me.")
        return jobs

    except Exception as e:
        print(f"❌ Error: {e}")
        os.makedirs("screenshots", exist_ok=True)
        driver.save_screenshot("screenshots/trademe_failed.png")
        driver.quit()
        return []
