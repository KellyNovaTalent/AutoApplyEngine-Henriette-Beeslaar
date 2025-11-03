"""
Education Gazette NZ job scraper using requests with browser headers.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from datetime import datetime
import time

BASE_URL = "https://gazette.education.govt.nz"
VACANCIES_API = f"{BASE_URL}/vacancies-2/"  # Alternative endpoint

# Browser headers to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def search_education_gazette(max_jobs: int = 50) -> List[Dict]:
    """Search Education Gazette for Foundation Phase jobs."""
    print(f"\n🔍 Searching Education Gazette NZ...")
    
    jobs_found = []
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # Try the main vacancies page with GET
        response = session.get(VACANCIES_API, timeout=30, allow_redirects=True)
        
        if response.status_code != 200:
            print(f"   ⚠️  Status {response.status_code}, trying alternative method...")
            # Try direct vacancy listings
            return scrape_recent_vacancies(session, max_jobs)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job listings
        job_links = soup.find_all('a', href=re.compile(r'/vacancies/\w+-'))
        
        print(f"   Found {len(job_links)} job listings")
        
        for link in job_links[:max_jobs]:
            try:
                job_url = link.get('href')
                if not job_url.startswith('http'):
                    job_url = BASE_URL + job_url
                
                job_data = fetch_full_job(session, job_url)
                
                if job_data and is_relevant_job(job_data):
                    jobs_found.append(job_data)
                    print(f"   ✅ {len(jobs_found)}. {job_data['job_title']}")
                
                time.sleep(0.5)  # Be polite
                
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                continue
        
        print(f"\n✅ Found {len(jobs_found)} relevant Foundation Phase jobs")
        return jobs_found
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def scrape_recent_vacancies(session, max_jobs: int) -> List[Dict]:
    """Scrape using known vacancy reference numbers."""
    print("   📋 Using alternative scraping method...")
    
    jobs = []
    
    # Try fetching specific recent vacancy pages
    # Format: /vacancies/REFERENCE-job-title/
    # We can construct these from the homepage or use a pattern
    
    try:
        # Get homepage to find recent vacancy references
        response = session.get(BASE_URL, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all vacancy links from homepage
        links = soup.find_all('a', href=re.compile(r'/vacancies/\w+'))
        
        for link in links[:max_jobs]:
            job_url = link.get('href')
            if job_url and '/vacancies/' in job_url:
                if not job_url.startswith('http'):
                    job_url = BASE_URL + job_url
                
                job_data = fetch_full_job(session, job_url)
                if job_data and is_relevant_job(job_data):
                    jobs.append(job_data)
                    print(f"   ✅ {len(jobs)}. {job_data['job_title']}")
                
                time.sleep(0.5)
        
    except Exception as e:
        print(f"   Error in alternative method: {e}")
    
    return jobs


def fetch_full_job(session, job_url: str) -> Optional[Dict]:
    """Fetch complete job details including email."""
    try:
        response = session.get(job_url, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1') or soup.find(class_='vacancy-title')
        job_title = title_elem.get_text(strip=True) if title_elem else "Teaching Position"
        
        # Extract school name
        school_elem = soup.find(class_='school-name') or soup.find('strong')
        company_name = school_elem.get_text(strip=True) if school_elem else "NZ School"
        
        # Extract full description
        content_elem = soup.find(class_='vacancy-content') or soup.find('article')
        description = content_elem.get_text(strip=True)[:2000] if content_elem else ""
        
        # Extract email - CRITICAL for auto-apply!
        email = extract_email_from_page(soup)
        
        # Extract location
        location = "New Zealand"
        location_patterns = ['Auckland', 'Wellington', 'Canterbury', 'Waikato', 'Bay of Plenty', 'Otago']
        for loc in location_patterns:
            if loc.lower() in description.lower():
                location = loc
                break
        
        job_data = {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'job_url': job_url,
            'description': description,
            'posted_date': datetime.now().strftime('%Y-%m-%d'),
            'source_platform': 'Education Gazette NZ',
            'salary_info': None,
            'contact_email': email  # This enables auto-email!
        }
        
        return job_data
        
    except Exception as e:
        print(f"   Error fetching {job_url}: {e}")
        return None


def extract_email_from_page(soup) -> Optional[str]:
    """Extract school contact email from job page."""
    full_text = soup.get_text()
    
    # Email patterns commonly used in Education Gazette
    patterns = [
        r'[Ee]mail[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'[Cc]ontact[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'[Aa]pply to[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.school\.nz)',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.edu\.nz)',
        r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            email = match.group(1)
            print(f"      📧 Email found: {email}")
            return email
    
    return None


def is_relevant_job(job: Dict) -> bool:
    """Filter for Foundation Phase/Junior Primary jobs."""
    title_lower = job['job_title'].lower()
    desc_lower = job['description'].lower()
    combined = title_lower + ' ' + desc_lower
    
    # Exclude
    exclude = ['secondary', 'high school', 'year 7', 'year 8', 'year 9', 
               'principal', 'deputy principal', 'intermediate']
    
    for term in exclude:
        if term in combined:
            return False
    
    # Include Foundation Phase keywords
    include = ['year 1', 'year 2', 'year 3', 'junior', 'foundation', 
               'new entrant', 'learning support', 'senco', 'special education',
               'primary', 'early childhood']
    
    for term in include:
        if term in combined:
            return True
    
    return 'teacher' in title_lower and 'primary' in combined


if __name__ == "__main__":
    jobs = search_education_gazette(max_jobs=10)
    print(f"\n📊 Results: {len(jobs)} jobs, {sum(1 for j in jobs if j.get('contact_email'))} with emails")
