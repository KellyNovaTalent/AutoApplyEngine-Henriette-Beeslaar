import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

def should_auto_reject(job_title: str) -> tuple[bool, Optional[str]]:
    """
    Check if a job should be auto-rejected based on title.
    Returns (should_reject, reason)
    
    Currently disabled - all jobs are analyzed by AI.
    """
    return False, None

def clean_text(text: str) -> str:
    """Clean up text by removing extra whitespace and newlines."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_url(text: str, platform: str) -> Optional[str]:
    """Extract job URL from text based on platform."""
    if platform == 'LinkedIn':
        match = re.search(r'https?://(?:www\.)?linkedin\.com/jobs/view/\d+', text)
        if match:
            return match.group(0)
    elif platform == 'Seek':
        match = re.search(r'https?://(?:www\.)?seek\.co\.nz/job/\d+', text)
        if match:
            return match.group(0)
    elif platform == 'Education Gazette':
        match = re.search(r'https?://(?:www\.)?gazette\.education\.govt\.nz/[^\s<>"]+', text)
        if match:
            return match.group(0)
    return None

def parse_linkedin_email(email_body: str, email_id: str) -> List[Dict[str, Any]]:
    """
    Parse LinkedIn job alert email and extract job details.
    LinkedIn can send digest emails with multiple jobs.
    """
    jobs = []
    soup = BeautifulSoup(email_body, 'html.parser')
    
    job_sections = soup.find_all('a', href=re.compile(r'linkedin\.com/jobs/view'))
    
    if not job_sections:
        job_sections = soup.find_all('td', class_=re.compile(r'job|listing'))
    
    if not job_sections:
        text = soup.get_text()
        urls = re.findall(r'https?://(?:www\.)?linkedin\.com/jobs/view/\d+', text)
        
        for url in urls:
            title_match = re.search(r'([^\n]+)\s+(?:at|@)\s+([^\n]+)', text)
            
            job_data = {
                'job_title': title_match.group(1).strip() if title_match else 'LinkedIn Job',
                'company_name': title_match.group(2).strip() if title_match else 'Unknown',
                'location': '',
                'description': '',
                'job_url': url,
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'source_platform': 'LinkedIn',
                'salary_info': None,
                'email_id': email_id,
                'status': 'new',
                'rejection_reason': None
            }
            
            should_reject, reason = should_auto_reject(job_data['job_title'])
            if should_reject:
                job_data['status'] = 'auto-rejected'
                job_data['rejection_reason'] = reason
            
            jobs.append(job_data)
    else:
        for section in job_sections:
            try:
                if section.name == 'a':
                    url = section.get('href', '')
                    if 'linkedin.com/jobs/view' not in url:
                        continue
                    
                    job_title = clean_text(section.get_text())
                    
                    parent = section.find_parent(['tr', 'td', 'div'])
                    company_name = 'Unknown'
                    location = ''
                    
                    if parent:
                        text_content = parent.get_text()
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        if len(lines) > 1:
                            company_name = lines[1] if len(lines) > 1 else 'Unknown'
                        if len(lines) > 2:
                            location = lines[2]
                    
                    job_data = {
                        'job_title': job_title or 'LinkedIn Job',
                        'company_name': company_name,
                        'location': location,
                        'description': '',
                        'job_url': url.split('?')[0],
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source_platform': 'LinkedIn',
                        'salary_info': None,
                        'email_id': email_id,
                        'status': 'new',
                        'rejection_reason': None
                    }
                    
                    should_reject, reason = should_auto_reject(job_data['job_title'])
                    if should_reject:
                        job_data['status'] = 'auto-rejected'
                        job_data['rejection_reason'] = reason
                    
                    jobs.append(job_data)
                    
            except Exception as e:
                print(f"Error parsing LinkedIn job section: {e}")
                continue
    
    return jobs

def parse_seek_email(email_body: str, email_id: str) -> List[Dict[str, Any]]:
    """
    Parse Seek NZ job alert email and extract job details.
    Seek usually sends individual job alerts.
    """
    jobs = []
    soup = BeautifulSoup(email_body, 'html.parser')
    
    job_title = 'Seek Job'
    company_name = 'Unknown'
    location = ''
    description = ''
    job_url = None
    salary_info = None
    
    links = soup.find_all('a', href=re.compile(r'seek\.co\.nz/job'))
    if links:
        job_url = links[0].get('href', '').split('?')[0]
        job_title_elem = links[0]
        job_title = clean_text(job_title_elem.get_text()) or 'Seek Job'
    
    text = soup.get_text()
    
    company_match = re.search(r'(?:at|@|Company:)\s*([^\n]+)', text, re.IGNORECASE)
    if company_match:
        company_name = clean_text(company_match.group(1))
    
    location_match = re.search(r'(?:Location:|in)\s*([^\n]+(?:NZ|New Zealand)[^\n]*)', text, re.IGNORECASE)
    if location_match:
        location = clean_text(location_match.group(1))
    
    salary_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|pa|p\.a\.|year))?', text)
    if salary_match:
        salary_info = salary_match.group(0)
    
    paragraphs = soup.find_all('p')
    if paragraphs:
        description_parts = [clean_text(p.get_text()) for p in paragraphs[:3]]
        description = ' '.join(description_parts)[:500]
    
    if job_url:
        job_data = {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'description': description,
            'job_url': job_url,
            'posted_date': datetime.now().strftime('%Y-%m-%d'),
            'source_platform': 'Seek NZ',
            'salary_info': salary_info,
            'email_id': email_id,
            'status': 'new',
            'rejection_reason': None
        }
        
        should_reject, reason = should_auto_reject(job_data['job_title'])
        if should_reject:
            job_data['status'] = 'auto-rejected'
            job_data['rejection_reason'] = reason
        
        jobs.append(job_data)
    
    return jobs

def parse_education_gazette_email(email_body: str, email_id: str) -> List[Dict[str, Any]]:
    """
    Parse Education Gazette NZ job alert email and extract job details.
    Education Gazette can send digest emails with multiple teaching positions.
    """
    jobs = []
    soup = BeautifulSoup(email_body, 'html.parser')
    
    # Find all links to gazette job postings
    gazette_links = soup.find_all('a', href=re.compile(r'gazette\.education\.govt\.nz'))
    
    if gazette_links:
        # Multiple job listings in email
        for link in gazette_links:
            url = link.get('href', '')
            if not url or 'unsubscribe' in url.lower() or 'subscription' in url.lower():
                continue
            
            job_title = clean_text(link.get_text()) or 'Education Gazette Job'
            
            # Try to find company/school name near the link
            parent = link.find_parent(['tr', 'td', 'div', 'p'])
            company_name = 'Unknown School'
            location = 'New Zealand'
            description = ''
            
            if parent:
                text_content = parent.get_text()
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                # Look for school/organization name
                for i, line in enumerate(lines):
                    if job_title in line and i + 1 < len(lines):
                        company_name = lines[i + 1]
                        break
                
                # Look for location
                location_match = re.search(r'(?:Location:|in)\s*([^\n]+)', text_content, re.IGNORECASE)
                if location_match:
                    location = clean_text(location_match.group(1))
                
                # Extract description
                description = clean_text(text_content)[:500]
            
            job_data = {
                'job_title': job_title,
                'company_name': company_name,
                'location': location,
                'description': description,
                'job_url': url.split('?')[0],
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'source_platform': 'Education Gazette NZ',
                'salary_info': None,
                'email_id': email_id,
                'status': 'new',
                'rejection_reason': None
            }
            
            should_reject, reason = should_auto_reject(job_data['job_title'])
            if should_reject:
                job_data['status'] = 'auto-rejected'
                job_data['rejection_reason'] = reason
            
            jobs.append(job_data)
    else:
        # Fallback: search for gazette URLs in plain text
        text = soup.get_text()
        urls = re.findall(r'https?://(?:www\.)?gazette\.education\.govt\.nz/[^\s<>"]+', text)
        
        for url in urls:
            if 'unsubscribe' in url.lower() or 'subscription' in url.lower():
                continue
            
            # Try to extract job title from nearby text
            url_index = text.find(url)
            context = text[max(0, url_index - 200):url_index]
            
            # Look for job title patterns
            title_match = re.search(r'([A-Z][^.\n]{10,80}(?:Teacher|Principal|Coordinator|Manager|Tutor|Lecturer))', context)
            job_title = title_match.group(1).strip() if title_match else 'Education Gazette Job'
            
            job_data = {
                'job_title': job_title,
                'company_name': 'Unknown School',
                'location': 'New Zealand',
                'description': '',
                'job_url': url.split('?')[0],
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'source_platform': 'Education Gazette NZ',
                'salary_info': None,
                'email_id': email_id,
                'status': 'new',
                'rejection_reason': None
            }
            
            should_reject, reason = should_auto_reject(job_data['job_title'])
            if should_reject:
                job_data['status'] = 'auto-rejected'
                job_data['rejection_reason'] = reason
            
            jobs.append(job_data)
    
    return jobs

def parse_job_alert_email(email_from: str, email_subject: str, email_body: str, email_id: str) -> List[Dict[str, Any]]:
    """
    Route email to appropriate parser based on sender AND content.
    Returns list of job dictionaries.
    """
    email_from_lower = email_from.lower()
    email_subject_lower = email_subject.lower()
    email_body_lower = email_body.lower()
    
    # Check for LinkedIn - by sender, subject, or content
    if ('linkedin' in email_from_lower or 
        'linkedin' in email_subject_lower or 
        'linkedin.com/jobs' in email_body_lower):
        print(f"📧 Parsing LinkedIn email: {email_subject[:60]}")
        jobs = parse_linkedin_email(email_body, email_id)
        print(f"   → Extracted {len(jobs)} LinkedIn jobs")
        return jobs
    
    # Check for Seek NZ - by sender, subject, or content
    elif ('seek' in email_from_lower or 
          'seek' in email_subject_lower or 
          'seek.co.nz/job' in email_body_lower):
        print(f"📧 Parsing Seek NZ email: {email_subject[:60]}")
        jobs = parse_seek_email(email_body, email_id)
        print(f"   → Extracted {len(jobs)} Seek jobs")
        return jobs
    
    # Check for Education Gazette - by sender, subject, or content
    elif ('gazette.education.govt.nz' in email_from_lower or 
          'education.govt.nz' in email_from_lower or
          'edgazette' in email_from_lower or
          'education gazette' in email_subject_lower or
          'gazette.education.govt.nz' in email_body_lower):
        print(f"📧 Parsing Education Gazette NZ email: {email_subject[:60]}")
        jobs = parse_education_gazette_email(email_body, email_id)
        print(f"   → Extracted {len(jobs)} Education Gazette jobs")
        return jobs
    
    else:
        print(f"⚠️  Unknown job alert source")
        print(f"   From: {email_from[:60]}")
        print(f"   Subject: {email_subject[:60]}")
        return []
