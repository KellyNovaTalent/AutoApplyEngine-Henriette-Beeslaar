import requests
from bs4 import BeautifulSoup
import csv
import re
import time

BASE_URL = "https://gazette.education.govt.nz"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_page(start):
    """Scrape one Gazette vacancy page for job links and metadata"""
    url = f"{BASE_URL}/vacancies/?start={start}#results" if start > 0 else f"{BASE_URL}/vacancies/"
    print(f"🔎 Scraping list: {url}")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []
    for job in soup.select("article.block-vacancy-featured"):
        title = job.select_one("h3.title").get_text(strip=True)
        employer = job.select_one("span.tag.bullet")
        employer = employer.get_text(strip=True) if employer else "N/A"
        emp_type = job.select_one("p.title-byline")
        emp_type = emp_type.get_text(strip=True) if emp_type else "N/A"
        closing = job.select_one("div.cal-icon.end")
        closing = closing.get_text(" ", strip=True) if closing else "N/A"
        link = job.select_one("a")["href"]

        jobs.append({
            "Title": title,
            "Employer": employer,
            "Employment Type": emp_type,
            "Closing": closing,
            "Link": f"{BASE_URL}{link}"
        })

    return jobs

def scrape_job_detail(job):
    """Visit job detail page and extract description, contact, email, phone"""
    try:
        response = requests.get(job["Link"], headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Description
        desc = soup.select_one("div.description")
        job["Description"] = desc.get_text(" ", strip=True) if desc else "N/A"

        # Contact block
        contact = soup.select_one("div.contact")
        contact_text = contact.get_text(" ", strip=True) if contact else ""
        job["Contact"] = contact_text if contact_text else "N/A"

        # Extract email + phone with regex
        text_blob = job.get("Description", "") + " " + contact_text
        email_match = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_blob)
        phone_match = re.findall(r"\+?\d[\d\s-]{7,}", text_blob)

        job["Email"] = email_match[0] if email_match else "N/A"
        job["Phone"] = phone_match[0] if phone_match else "N/A"

    except Exception as e:
        print(f"⚠️ Error scraping {job['Link']}: {e}")
        job["Description"] = job["Contact"] = job["Email"] = job["Phone"] = "N/A"

    return job

def scrape_all():
    """Scrape all pages and job details"""
    all_jobs = []
    start = 0
    while True:
        jobs = scrape_page(start)
        if not jobs:
            break
        for job in jobs:
            print(f"   📝 Scraping details: {job['Title']} ({job['Employer']})")
            job = scrape_job_detail(job)
            all_jobs.append(job)
            time.sleep(1)  # be polite, avoid hammering server
        start += 10
    return all_jobs

if __name__ == "__main__":
    jobs = scrape_all()

    if jobs:
        with open("millicent_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)
        print(f"\n✅ Saved {len(jobs)} jobs with details into millicent_jobs.csv")
    else:
        print("⚠️ No jobs found")
