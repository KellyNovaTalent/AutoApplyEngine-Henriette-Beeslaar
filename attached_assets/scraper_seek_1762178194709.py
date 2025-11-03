import time, logging
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logger = logging.getLogger("job-scraper")

def _make_driver():
    opts = Options()
    # Show Chrome (not headless)
    # opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(60)
    print("Chrome launched OK")
    return driver

def _parse_seek_list(html: str):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Find job cards
    cards = soup.select("[data-automation='searchResults'] article, article") \
         or soup.select("a[href*='/job/'], [data-automation='job-card']")

    for card in cards:
        # Job title
        title_el = card.select_one("[data-automation='jobTitle']") or card.select_one("a[data-automation]")
        title = (title_el.get_text(strip=True) if title_el else "") or (card.get("aria-label") or "").strip()

        # Job link
        link = ""
        if title_el and title_el.get("href"):
            href = title_el["href"]
            link = href if href.startswith("http") else f"https://www.seek.co.nz{href}"

        # Company name (fixed to pull nested text)
        company_el = card.select_one("[data-automation='advertiser-name']")
        company = company_el.get_text(" ", strip=True) if company_el else "Unknown"

        # Location
        loc_el = card.select_one("[data-automation='jobLocation']")
        location = loc_el.get_text(strip=True) if loc_el else ""

        # Posted date
        posted_el = card.select_one("[data-automation='jobListingDate']")
        posted = posted_el.get_text(strip=True) if posted_el else ""

        if title and link:
            jobs.append({
                "Source": "Seek",
                "Position Title": title,
                "Company Name": company,
                "Location": location,
                "Posted": posted,
                "Application Weblink": link,
            })

    return jobs

def scrape_seek(query: str):
    if not query:
        return []

    driver = _make_driver()
    try:
        url = f"https://www.seek.co.nz/{quote_plus(query)}-jobs"
        logger.info(f"Seek URL: {url}")
        print(f"Opening {url}")
        try:
            driver.get(url)
        except TimeoutException:
            logger.warning("Seek took too long to load, continuing...")
        time.sleep(3.5)

        jobs = _parse_seek_list(driver.page_source)

        # Keep clicking "Load more jobs" until it disappears
        while True:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "[data-automation='searchMoreJobs']")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(4)
                more = _parse_seek_list(driver.page_source)
                seen = {j["Application Weblink"] for j in jobs}
                for j in more:
                    if j["Application Weblink"] not in seen:
                        jobs.append(j)
                print(f"Loaded {len(jobs)} jobs so far...")
            except Exception:
                break

        print(f"Finished loading {len(jobs)} total jobs from Seek")
        return jobs

    finally:
        try:
            driver.quit()
        except Exception:
            pass
