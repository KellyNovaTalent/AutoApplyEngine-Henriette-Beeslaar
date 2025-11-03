import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
import fitz  # PyMuPDF for PDF text extraction
from io import BytesIO
import time

# --- Helpers ---
def extract_emails(text):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

def extract_phones(text):
    return re.findall(r"\(?\d{2,4}\)?[-\s]?\d{3}[-\s]?\d{3,4}", text)

def extract_from_pdf(url):
    emails, phones = [], []
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        pdf_data = BytesIO(resp.content)
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        emails = extract_emails(text)
        phones = extract_phones(text)
    except Exception as e:
        print(f"   ⚠️ Could not read PDF {url}: {e}")
    return emails, phones

# --- Main enrichment ---
def enrich_jobs(input_csv="millicent_jobs_filtered.csv", output_csv="millicent_jobs_with_emails.csv", limit=None):
    jobs = pd.read_csv(input_csv)
    if limit:
        jobs = jobs.head(limit)
    enriched = []

    for idx, row in jobs.iterrows():
        title, employer, job_url = row["Title"], row["Employer"], row["Link"]
        print(f"[{idx+1}/{len(jobs)}] 🔎 Enriching: {title} | {job_url}")

        all_emails, all_phones = [], []

        try:
            resp = requests.get(job_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Emails from mailto links
            for a in soup.select("a[href^=mailto]"):
                email = a["href"].replace("mailto:", "").split("?")[0]
                all_emails.append(email)

            # Text search
            page_text = soup.get_text(separator=" ", strip=True)
            all_emails.extend(extract_emails(page_text))
            all_phones.extend(extract_phones(page_text))

            # PDFs
            for a in soup.find_all("a", href=True):
                if a["href"].lower().endswith(".pdf"):
                    pdf_url = a["href"]
                    if pdf_url.startswith("/"):
                        pdf_url = "https://gazette.education.govt.nz" + pdf_url
                    print(f"   📎 Reading PDF: {pdf_url}")
                    pdf_emails, pdf_phones = extract_from_pdf(pdf_url)
                    all_emails.extend(pdf_emails)
                    all_phones.extend(pdf_phones)

        except Exception as e:
            print(f"   ⚠️ Skipping {job_url} due to error: {e}")

        # Deduplicate
        all_emails = sorted(set([e for e in all_emails if e.strip()]))
        all_phones = sorted(set([p for p in all_phones if p.strip()]))

        if all_emails:
            print(f"   📧 Found: {all_emails}")
        if all_phones:
            print(f"   ☎️ Found: {all_phones}")

        enriched.append({
            "Title": title,
            "Employer": employer,
            "Link": job_url,
            "Emails": "; ".join(all_emails),
            "Phones": "; ".join(all_phones),
        })

        # Small delay to avoid hammering the site
        time.sleep(1)

    # Save results
    pd.DataFrame(enriched).to_csv(output_csv, index=False, encoding="utf-8")
    print(f"\n✅ Finished — saved {len(enriched)} jobs into {output_csv}")

# --- Run ---
if __name__ == "__main__":
    enrich_jobs(
        input_csv="millicent_jobs_filtered.csv",   # 👈 only the 360 filtered jobs
        output_csv="millicent_jobs_with_emails.csv",
        limit=None                                # change to e.g. 5 for testing
    )
