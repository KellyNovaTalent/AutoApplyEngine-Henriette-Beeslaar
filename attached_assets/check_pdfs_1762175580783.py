import csv
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

input_file = "millicent_jobs.csv"

with open(input_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    jobs = list(reader)[:5]  # just first 5 jobs for test

for job in jobs:
    url = job["Link"]
    print(f"\n🔎 Checking PDFs for: {job['Title']} | {url}")
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    pdf_links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].lower().endswith(".pdf")]
    if pdf_links:
        for pdf in pdf_links:
            if not pdf.startswith("http"):
                pdf = "https://gazette.education.govt.nz" + pdf
            print(f"   📎 Found PDF: {pdf}")
    else:
        print("   ⚠️ No PDFs found on this page")
