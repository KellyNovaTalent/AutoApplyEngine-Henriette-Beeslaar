import csv
from datetime import datetime
from pathlib import Path

from scraper_seek import scrape_seek
from scraper_trademe import scrape_trademe
from scraper_indeed import scrape_indeed
from scraper_glassdoor import scrape_glassdoor

def save_jobs_to_csv(jobs, filename):
    if not jobs:
        print("?? No jobs to save.")
        return
    keys = jobs[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(jobs)
    print(f"? Saved {len(jobs)} jobs to {filename}")

def run_all_scrapers(query: str):
    all_jobs = []
    print(f"?? Searching for jobs with query: {query}")
    
    try:
        all_jobs.extend(scrape_seek(query))
    except Exception as e:
        print(f"?? Seek failed: {e}")
    try:
        all_jobs.extend(scrape_trademe(query))
    except Exception as e:
        print(f"?? TradeMe failed: {e}")
    try:
        all_jobs.extend(scrape_indeed(query))
    except Exception as e:
        print(f"?? Indeed failed: {e}")
    try:
        all_jobs.extend(scrape_glassdoor(query))
    except Exception as e:
        print(f"?? Glassdoor failed: {e}")

    if all_jobs:
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        out_path = Path("results") / f"{query.replace(' ', '_')}_jobs_{ts}.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        save_jobs_to_csv(all_jobs, out_path)
    else:
        print("? No jobs found at all.")

if __name__ == "__main__":
    query = input("Enter job search query: ").strip()
    run_all_scrapers(query)
