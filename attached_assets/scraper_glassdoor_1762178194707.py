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

def scrape_glassdoor(query: str) -> List[Dict]:
    base_url = "https://www.glassdoor.co.nz/Job/jobs.htm?sc.keyword="
    url = base_url + query.replace(" ", "%20")
    driver = _make_driver()
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    jobs = []
    listings = soup.select("li.react-job-listing")

    for listing in listings:
        title_el = listing.select_one("a[data-test='job-link']")
        company_el = listing.select_one("div.jobHeader a")
        location_el = listing.select_one("span.pr-xxsm")
        date_el = listing.select_one("div.d-flex.align-items-end.pl-std.css-mi55ob")

        jobs.append({
            "Source": "Glassdoor",
            "Position Title": title_el.get_text(strip=True) if title_el else "",
            "Company Name": company_el.get_text(strip=True) if company_el else "",
            "Location": location_el.get_text(strip=True) if location_el else "",
            "Posted": date_el.get_text(strip=True) if date_el else "",
            "Application Weblink": "https://www.glassdoor.co.nz" + title_el['href'] if title_el else "",
        })

    return jobs