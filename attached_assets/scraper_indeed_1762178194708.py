import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def _make_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_indeed(query: str) -> List[Dict]:
    base_url = "https://nz.indeed.com/jobs?q="
    url = base_url + query.replace(" ", "+")
    driver = _make_driver()
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    jobs = []
    listings = soup.select("div.job_seen_beacon")

    for listing in listings:
        title_el = listing.select_one("h2.jobTitle > a")
        company_el = listing.select_one("span.companyName")
        location_el = listing.select_one("div.companyLocation")
        date_el = listing.select_one("span.date")

        jobs.append({
            "Source": "Indeed",
            "Position Title": title_el.get_text(strip=True) if title_el else "",
            "Company Name": company_el.get_text(strip=True) if company_el else "",
            "Location": location_el.get_text(strip=True) if location_el else "",
            "Posted": date_el.get_text(strip=True) if date_el else "",
            "Application Weblink": "https://nz.indeed.com" + title_el['href'] if title_el else "",
        })

    return jobs