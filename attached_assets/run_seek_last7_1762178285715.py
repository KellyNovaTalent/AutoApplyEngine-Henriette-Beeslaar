import re
import time
import random
import csv
from datetime import datetime
from pathlib import Path

from scraper_seek import scrape_seek
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')

def _make_driver():
    opts = Options()
    # Show Chrome (not headless)
    # opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(60)
    return driver

def _posted_within_7_days(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    if 'today' in t or 'hour' in t:
        return True
    m = re.search(r'(\d+)', t)
    if not m:
        return False
    days = int(m.group(1))
    return days <= 7

def enrich_with_details(jobs):
    if not jobs:
        return jobs
    driver = _make_driver()
    try:
        for idx, j in enumerate(jobs, start=1):
            j['Email'] = ''
            j['Phone'] = ''
            j['Description'] = ''
            url = j.get('Application Weblink', '')
            if not url:
                continue
            try:
                print(f"Visiting job {idx} of {len(jobs)}: {j.get('Position Title','')} @ {j.get('Company Name','')}")
                driver.get(url)

                # Human-like behaviour
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                wait_time = random.randint(45, 75)
                print(f'   Waiting {wait_time}s on page...')
                time.sleep(wait_time)

                html = driver.page_source or ''
                soup = BeautifulSoup(html, 'html.parser')

                # Company name (fill in if missing)
                if not j.get('Company Name') or j['Company Name'] == "Unknown":
                    comp_el = soup.select_one("[data-automation='advertiser-name']")
                    if comp_el:
                        j['Company Name'] = comp_el.get_text(" ", strip=True)
                    else:
                        btn_span = soup.select_one("div button span")
                        if btn_span:
                            j['Company Name'] = btn_span.get_text(strip=True)

                # Email
                mailto_links = soup.select("a[href^='mailto:']")
                if mailto_links:
                    j['Email'] = mailto_links[0].get('href').replace('mailto:', '').strip()
                else:
                    m = EMAIL_REGEX.search(html)
                    if m:
                        j['Email'] = m.group(0)

                # Phone
                phone_links = soup.select("a[href^='tel:']")
                if phone_links:
                    j['Phone'] = phone_links[0].get('href').replace('tel:', '').strip()

                # Description
                desc_container = soup.select_one("div[data-automation='jobAdDetails']") or soup
                ps = desc_container.find_all('p')
                description_text = ' '.join(p.get_text(' ', strip=True) for p in ps)
                j['Description'] = description_text.strip()[:1000]

                print(f"Finished job {idx} of {len(jobs)}")

            except Exception as e:
                print(f"Failed job {idx}: {e}")
                continue

            # Pause before next job
            pause = random.randint(10, 20)
            print(f'   Sleeping {pause}s before next job...')
            time.sleep(pause)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return jobs

def save_csv(jobs, query):
    out_dir = Path('results')
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M')
    safe_query = query.replace(' ', '_').lower()
    out_path = out_dir / f'seek_{safe_query}_last7_{ts}.csv'

    rows = []
    for j in jobs:
        rows.append({
            'Hiring Company': j.get('Company Name', ''),
            'Position': j.get('Position Title', ''),
            'Application Link': j.get('Application Weblink', ''),
            'Email': j.get('Email', ''),
            'Phone': j.get('Phone', ''),
            'Description': j.get('Description', ''),
        })

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Hiring Company','Position','Application Link','Email','Phone','Description'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} jobs to {out_path}")

def main():
    query = input('Enter job search query (e.g. Plumber, Teacher, Electrician): ').strip()
    if not query:
        print('No query provided, exiting.')
        return
    print(f"\nSeek NZ | Query: {query} | Filtering last 7 days")
    jobs = scrape_seek(query)

    print(f"Total jobs found on Seek: {len(jobs)}")
    recent = [j for j in jobs if _posted_within_7_days(j.get('Posted', ''))]
    print(f"Jobs within last 7 days: {len(recent)}\n")

    recent = enrich_with_details(recent)
    save_csv(recent, query)

if __name__ == '__main__':
    main()
