import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
from datetime import datetime

def fetch_job_from_url(url: str) -> Optional[Dict]:
    """
    Fetch job details from a job posting URL.
    Supports LinkedIn, Seek NZ, and Education Gazette NZ.
    """
    try:
        # Determine platform from URL
        if 'linkedin.com' in url:
            return fetch_linkedin_job(url)
        elif 'seek.co.nz' in url:
            return fetch_seek_job(url)
        elif 'gazette.education.govt.nz' in url or 'edgazette.govt.nz' in url:
            return fetch_education_gazette_job(url)
        else:
            return {
                'job_title': 'Unknown Job',
                'company_name': 'Unknown Company',
                'location': 'Unknown',
                'description': 'Could not determine job platform',
                'job_url': url,
                'source_platform': 'Other',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'salary_info': None
            }
    except Exception as e:
        print(f"Error fetching job from {url}: {e}")
        return None

def fetch_linkedin_job(url: str) -> Optional[Dict]:
    """Fetch job details from LinkedIn."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract job title
        title_elem = soup.find('h1') or soup.find('h2', class_=re.compile('job|title'))
        job_title = title_elem.get_text(strip=True) if title_elem else 'LinkedIn Job'
        
        # Extract company name
        company_elem = soup.find('a', class_=re.compile('company')) or soup.find('span', class_=re.compile('company'))
        company_name = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
        
        # Extract location
        location_elem = soup.find('span', class_=re.compile('location')) or soup.find('div', class_=re.compile('location'))
        location = location_elem.get_text(strip=True) if location_elem else ''
        
        # Extract description
        desc_elem = soup.find('div', class_=re.compile('description')) or soup.find('article')
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ''
        
        return {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'description': description,
            'job_url': url,
            'source_platform': 'LinkedIn',
            'posted_date': datetime.now().strftime('%Y-%m-%d'),
            'salary_info': None
        }
    except Exception as e:
        print(f"Error fetching LinkedIn job: {e}")
        return None

def fetch_seek_job(url: str) -> Optional[Dict]:
    """Fetch job details from Seek NZ."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract job title
        title_elem = soup.find('h1') or soup.find('h1', attrs={'data-automation': 'job-detail-title'})
        job_title = title_elem.get_text(strip=True) if title_elem else 'Seek Job'
        
        # Extract company name
        company_elem = soup.find('span', attrs={'data-automation': 'advertiser-name'}) or soup.find('a', class_=re.compile('company'))
        company_name = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
        
        # Extract location
        location_elem = soup.find('span', attrs={'data-automation': 'job-detail-location'}) or soup.find('span', class_=re.compile('location'))
        location = location_elem.get_text(strip=True) if location_elem else ''
        
        # Extract salary
        salary_elem = soup.find('span', attrs={'data-automation': 'job-detail-salary'})
        salary_info = salary_elem.get_text(strip=True) if salary_elem else None
        
        # Extract description
        desc_elem = soup.find('div', attrs={'data-automation': 'jobAdDetails'}) or soup.find('div', class_=re.compile('content'))
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ''
        
        return {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'description': description,
            'job_url': url,
            'source_platform': 'Seek NZ',
            'posted_date': datetime.now().strftime('%Y-%m-%d'),
            'salary_info': salary_info
        }
    except Exception as e:
        print(f"Error fetching Seek job: {e}")
        return None

def fetch_education_gazette_job(url: str) -> Optional[Dict]:
    """Fetch job details from Education Gazette NZ."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract job title
        title_elem = soup.find('h1') or soup.find('h2')
        job_title = title_elem.get_text(strip=True) if title_elem else 'Education Gazette Job'
        
        # Extract school/organization
        company_elem = soup.find('div', class_=re.compile('school|organization|employer'))
        company_name = company_elem.get_text(strip=True) if company_elem else 'Unknown School'
        
        # Extract location
        location_match = re.search(r'Location[:\s]+([^\n]+)', soup.get_text())
        location = location_match.group(1).strip() if location_match else 'New Zealand'
        
        # Extract description
        desc_elem = soup.find('div', class_=re.compile('description|content|details'))
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else soup.get_text(strip=True)[:1000]
        
        return {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'description': description,
            'job_url': url,
            'source_platform': 'Education Gazette NZ',
            'posted_date': datetime.now().strftime('%Y-%m-%d'),
            'salary_info': None
        }
    except Exception as e:
        print(f"Error fetching Education Gazette job: {e}")
        return None
