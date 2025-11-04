"""
Education Gazette NZ job scraper - Based on user's proven working scraper.
Official NZ government teaching job board with school email addresses.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from datetime import datetime
import time

BASE_URL = "https://gazette.education.govt.nz"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def search_education_gazette(max_jobs: int = 50) -> List[Dict]:
    """
    Search Education Gazette for Foundation Phase teaching jobs.
    Based on proven scraper pattern with requests + BeautifulSoup.
    
    Returns empty list if scraping fails (fault-tolerant).
    """
    print(f"\n📰 Searching Education Gazette NZ (Official Government Job Board)...")
    
    all_jobs = []
    start = 0
    pages_scraped = 0
    max_pages = 5
    
    try:
        while pages_scraped < max_pages and len(all_jobs) < max_jobs:
            url = f"{BASE_URL}/vacancies/?start={start}#results" if start > 0 else f"{BASE_URL}/vacancies/"
            print(f"   🔎 Page {pages_scraped + 1}: Fetching jobs...")
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                jobs_on_page = soup.select("article.block-vacancy-featured")
                
                if not jobs_on_page:
                    print(f"   ℹ️  No more jobs found")
                    break
                
                print(f"   Found {len(jobs_on_page)} job listings on this page")
                
                for job_card in jobs_on_page:
                    if len(all_jobs) >= max_jobs:
                        break
                    
                    try:
                        job_data = scrape_job_from_card(job_card)
                        
                        if job_data and is_relevant_job(job_data):
                            all_jobs.append(job_data)
                            print(f"   ✅ {len(all_jobs)}. {job_data['job_title']} - {job_data['company_name']}")
                            if job_data.get('contact_email'):
                                print(f"      📧 Email: {job_data['contact_email']}")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"   ⚠️  Error scraping job card: {e}")
                        continue
                
                start += 10
                pages_scraped += 1
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  Page request failed: {e}")
                break
        
        print(f"\n✅ Education Gazette: Found {len(all_jobs)} relevant Foundation Phase jobs")
        if all_jobs:
            email_count = sum(1 for j in all_jobs if j.get('contact_email'))
            print(f"   Jobs with email addresses: {email_count}/{len(all_jobs)}")
        
        return all_jobs
        
    except Exception as e:
        print(f"   ❌ Education Gazette search failed: {e}")
        print(f"   Continuing with LinkedIn + Seek only...")
        return []


def scrape_job_from_card(card) -> Optional[Dict]:
    """Extract job data from listing card and fetch full details."""
    try:
        title_elem = card.select_one("h3.title")
        job_title = title_elem.get_text(strip=True) if title_elem else None
        
        if not job_title:
            return None
        
        employer_elem = card.select_one("span.tag.bullet")
        company_name = employer_elem.get_text(strip=True) if employer_elem else "NZ School"
        
        emp_type_elem = card.select_one("p.title-byline")
        employment_type = emp_type_elem.get_text(strip=True) if emp_type_elem else "Full time"
        
        closing_elem = card.select_one("div.cal-icon.end")
        closing_date = closing_elem.get_text(" ", strip=True) if closing_elem else None
        
        link_elem = card.select_one("a")
        job_url = link_elem["href"] if link_elem and link_elem.get("href") else None
        
        if not job_url:
            return None
        
        if not job_url.startswith("http"):
            job_url = BASE_URL + job_url
        
        job_details = fetch_job_details(job_url)
        
        job_data = {
            'job_title': job_title,
            'company_name': company_name,
            'location': extract_location(job_details.get('description', '')),
            'job_url': job_url,
            'description': job_details.get('description', ''),
            'posted_date': closing_date or datetime.now().strftime('%Y-%m-%d'),
            'source_platform': 'Education Gazette NZ',
            'salary_info': None,
            'contact_email': job_details.get('email')
        }
        
        return job_data
        
    except Exception as e:
        return None


def fetch_job_details(job_url: str) -> Dict:
    """
    Visit job detail page and extract description, contact info, email.
    This is the KEY function - Education Gazette pages have school emails!
    """
    details = {
        'description': '',
        'email': None,
        'contact': ''
    }
    
    try:
        response = requests.get(job_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        desc_elem = soup.select_one("div.description")
        if desc_elem:
            details['description'] = desc_elem.get_text(" ", strip=True)[:2000]
        
        contact_elem = soup.select_one("div.contact")
        contact_text = contact_elem.get_text(" ", strip=True) if contact_elem else ""
        details['contact'] = contact_text
        
        text_blob = details['description'] + " " + contact_text
        
        email_matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_blob)
        if email_matches:
            details['email'] = email_matches[0]
        
    except Exception as e:
        pass
    
    return details


def extract_location(description: str) -> str:
    """Extract location from job description."""
    locations = [
        'Auckland', 'Wellington', 'Canterbury', 'Christchurch', 
        'Waikato', 'Hamilton', 'Bay of Plenty', 'Tauranga',
        'Otago', 'Dunedin', 'Manawatu', 'Palmerston North',
        'Hawke\'s Bay', 'Napier', 'Taranaki', 'New Plymouth',
        'Nelson', 'Marlborough', 'Gisborne', 'Northland',
        'Whangarei', 'Southland', 'Invercargill'
    ]
    
    for location in locations:
        if location.lower() in description.lower():
            return location
    
    return "New Zealand"


def is_relevant_job(job: Dict) -> bool:
    """
    Filter for Foundation Phase / Junior Primary teaching jobs (Years R-3).
    Exclude secondary, intermediate, and administrative positions.
    """
    title_lower = job['job_title'].lower()
    desc_lower = job['description'].lower()
    combined = title_lower + ' ' + desc_lower
    
    exclude_keywords = [
        'secondary', 'high school', 
        'year 7', 'year 8', 'year 9', 'year 10', 'year 11', 'year 12', 'year 13',
        'intermediate', 'middle school',
        'principal', 'deputy principal', 'assistant principal',
        'head of department', 'hod', 'dean'
    ]
    
    for keyword in exclude_keywords:
        if keyword in combined:
            return False
    
    include_keywords = [
        'year 1', 'year 2', 'year 3', 'year 0',
        'years 1-3', 'years 1-4', 'years 0-3',
        'junior', 'foundation', 'new entrant',
        'learning support', 'senco', 'special education',
        'primary', 'early childhood', 'ece', 'ecd',
        'grade r', 'grade 1', 'grade 2', 'grade 3'
    ]
    
    for keyword in include_keywords:
        if keyword in combined:
            return True
    
    if 'teacher' in title_lower and 'primary' in combined:
        return True
    
    return False


if __name__ == "__main__":
    print("Testing Education Gazette scraper with user's proven approach...")
    jobs = search_education_gazette(max_jobs=15)
    
    print(f"\n📊 Test Results:")
    print(f"   Total jobs found: {len(jobs)}")
    print(f"   Jobs with email: {sum(1 for j in jobs if j.get('contact_email'))}")
    
    if jobs:
        print(f"\n📋 Sample job:")
        sample = jobs[0]
        for key, value in sample.items():
            if value:
                display_value = str(value)[:100]
                print(f"   {key}: {display_value}")
