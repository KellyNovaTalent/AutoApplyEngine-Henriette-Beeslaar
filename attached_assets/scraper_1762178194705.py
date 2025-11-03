import time, random, csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

def _init_driver():
    options = Options()
    options.add_argument("--user-data-dir=C:\\Temp\\UniqueChromeProfile")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver

def _scrape_seek_with_driver(driver, query, location=None, max_pages=1, timeout=10, delay_range=(2, 4)):
    results = []
    seen_urls = set()
    base = f"https://www.seek.co.nz/{query.replace(' ', '-')}-jobs"
    if location:
        base += f"/in-{location.replace(' ', '-')}"

    for attempt in range(3):
        try:
            driver.get(base)
            WebDriverWait(driver, timeout).until(lambda d: (
                d.find_elements(By.CSS_SELECTOR, 'article[data-automation="normalJob"]') or
                "no results" in d.page_source.lower()
            ))
            break
        except TimeoutException:
            if attempt == 2:
                return []
            time.sleep(5)

    for page in range(1, max_pages + 1):
        print(f"\n📄 [Seek] Page {page}")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select('article[data-automation="normalJob"], article[data-automation="premiumJob"]')

        if not cards:
            break

        for card in cards:
            try:
                title = card.select_one('[data-automation="jobTitle"]')
                company = card.select_one('[data-automation="jobCompany"]')
                loc = card.select_one('[data-automation="jobLocation"]')
                salary = card.select_one('[data-automation="jobSalary"]')
                date = card.select_one('[data-automation="jobListingDate"]')
                link = card.find("a", href=True)
                url = f"https://www.seek.co.nz{link['href']}" if link else ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                results.append({
                    "job_title": title.get_text(strip=True) if title else "",
                    "company": company.get_text(strip=True) if company else "",
                    "location": loc.get_text(strip=True) if loc else "",
                    "salary": salary.get_text(strip=True) if salary else "",
                    "description": card.get_text(" ", strip=True)[:250],
                    "url": url,
                    "job_type": "",
                    "posted_date": date.get_text(strip=True) if date else "",
                    "source": "Seek"
                })
                print(f"✅ {results[-1]['job_title']} | {results[-1]['location']}")
            except Exception:
                continue

        if page < max_pages:
            try:
                next_btn = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-automation="page-next"]'))
                )
                next_btn.click()
                time.sleep(random.uniform(*delay_range))
            except:
                break

    return results

def _scrape_trademe_with_driver(driver, query, max_pages=1, timeout=10, delay_range=(2, 4)):
    results = []
    seen_urls = set()
    search = query.replace(" ", "+")
    url = f"https://www.trademe.co.nz/a/jobs/search?search_string={search}"
    driver.get(url)

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tm-promoted-listing-card__listing-info"))
        )
    except TimeoutException:
        print("⚠️ TradeMe: No listings found.")
        return []

    for page in range(1, max_pages + 1):
        print(f"\n📄 [TradeMe] Page {page}")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select("div.tm-promoted-listing-card__listing-info a.tm-promoted-listing-card__title")

        if not cards:
            break

        for tag in cards:
            href = tag.get("href")
            if not href:
                continue
            full_url = f"https://www.trademe.co.nz{href}"
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            results.append({
                "job_title": tag.get_text(strip=True),
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": full_url,
                "job_type": "",
                "posted_date": "",
                "source": "TradeMe"
            })
            print(f"✅ {results[-1]['job_title']}")

        try:
            next_btn = driver.find_element(By.XPATH, '//a[contains(@href, "page=") and contains(text(), "Next")]')
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(random.uniform(*delay_range))
        except NoSuchElementException:
            break

    return results

def scrape_all(query, location=None, max_pages=1):
    driver = _init_driver()
    results = []
    try:
        results += _scrape_seek_with_driver(driver, query, location, max_pages)
        results += _scrape_trademe_with_driver(driver, query, max_pages)
    finally:
        driver.quit()
    return results

def export_to_csv(jobs, filename="jobs.csv"):
    if not jobs:
        print("⚠️ No jobs to export.")
        return

    fieldnames = list(jobs[0].keys())
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)
    print(f"✅ CSV saved to: {filename}")