import os
from typing import Dict, Optional, List
from datetime import datetime
from apify_client import ApifyClient

APIFY_API_KEY = os.environ.get('APIFY_API_KEY')

def search_jobs_apify(keywords: str, location: str = "New Zealand", max_jobs: int = 50, platform: str = "both", remote_only: bool = False) -> List[Dict]:
    """
    Search for jobs using Apify scrapers.
    
    Args:
        keywords: Job keywords/titles to search for
        location: Job location (default: New Zealand)
        max_jobs: Maximum number of jobs to return (default: 50)
        platform: 'linkedin', 'seek', or 'both' (default: both)
        remote_only: Filter for remote jobs only (default: False)
    
    Returns:
        List of job dictionaries with standardized fields
    """
    if not APIFY_API_KEY:
        print("❌ ERROR: APIFY_API_KEY not found in environment")
        raise ValueError("APIFY_API_KEY environment variable is required for job search")
    
    client = ApifyClient(APIFY_API_KEY)
    all_jobs = []
    errors = []
    
    if platform in ['linkedin', 'both']:
        try:
            linkedin_jobs = search_linkedin_jobs(client, keywords, location, max_jobs // 2 if platform == 'both' else max_jobs, remote_only)
            all_jobs.extend(linkedin_jobs)
        except Exception as e:
            errors.append(f"LinkedIn: {str(e)}")
            print(f"❌ LinkedIn search error: {e}")
            if platform == 'linkedin':
                raise
    
    if platform in ['seek', 'both']:
        try:
            seek_jobs = search_seek_jobs(client, keywords, location, max_jobs // 2 if platform == 'both' else max_jobs, remote_only)
            all_jobs.extend(seek_jobs)
        except Exception as e:
            errors.append(f"Seek: {str(e)}")
            print(f"❌ Seek search error: {e}")
            if platform == 'seek':
                raise
    
    if not all_jobs and errors:
        error_msg = f"All searches failed - {'; '.join(errors)}"
        print(f"⚠️  {error_msg}")
        raise ValueError(error_msg)
    
    return all_jobs[:max_jobs]


def search_linkedin_jobs(client: ApifyClient, keywords: str, location: str, max_jobs: int, remote_only: bool = False) -> List[Dict]:
    """Search LinkedIn jobs using Apify actor bebity/linkedin-jobs-scraper."""
    print(f"🔍 Searching LinkedIn for '{keywords}' in {location}...")
    
    run_input = {
        "keywords": keywords,
        "location": location,
        "maxItems": max_jobs,
        "remote": "Remote" if remote_only else "Any"
    }
    
    run = client.actor("bebity/linkedin-jobs-scraper").call(run_input=run_input)
    
    if not run or "defaultDatasetId" not in run:
        print("❌ LinkedIn scraper run failed - no dataset returned")
        raise ValueError("LinkedIn actor returned no dataset - check actor ID and input parameters")
    
    jobs = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        job_data = {
            'job_title': item.get('job_title', item.get('title', 'Unknown Job')),
            'company_name': item.get('company', item.get('company_name', 'Unknown Company')),
            'location': item.get('location', location),
            'description': item.get('description', item.get('job_description', ''))[:1000],
            'job_url': item.get('job_url', item.get('url', '')),
            'source_platform': 'LinkedIn',
            'posted_date': item.get('posted_date', datetime.now().strftime('%Y-%m-%d')),
            'salary_info': item.get('salary', item.get('compensation', None)),
            'employment_type': item.get('employment_type', item.get('job_type', None)),
            'experience_level': item.get('experience_level', None),
            'applicants_count': item.get('applicants', item.get('num_applicants', None))
        }
        jobs.append(job_data)
    
    print(f"✅ Found {len(jobs)} LinkedIn jobs")
    return jobs


def search_seek_jobs(client: ApifyClient, keywords: str, location: str, max_jobs: int, remote_only: bool = False) -> List[Dict]:
    """Search Seek NZ jobs using Apify actor websift/seek-job-scraper."""
    print(f"🔍 Searching Seek for '{keywords}' in {location}...")
    
    run_input = {
        "keyword": keywords,
        "place": location.lower().replace('new zealand', 'new-zealand'),
        "maxItems": max_jobs,
        "workType": "Any"
    }
    
    run = client.actor("websift/seek-job-scraper").call(run_input=run_input)
    
    if not run or "defaultDatasetId" not in run:
        print("❌ Seek scraper run failed - no dataset returned")
        raise ValueError("Seek actor returned no dataset - check actor ID and input parameters")
    
    jobs = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        # Filter for remote jobs if requested
        if remote_only:
            work_arrangement = item.get('workArrangement', '').lower()
            if 'remote' not in work_arrangement and 'work from home' not in work_arrangement:
                continue
        
        job_data = {
            'job_title': item.get('title', item.get('job_title', 'Unknown Job')),
            'company_name': item.get('company', item.get('advertiser', 'Unknown Company')),
            'location': item.get('location', item.get('suburb', location)),
            'description': item.get('description', item.get('teaser', ''))[:1000],
            'job_url': item.get('jobUrl', item.get('url', '')),
            'source_platform': 'Seek NZ',
            'posted_date': item.get('listedDate', item.get('posted_date', datetime.now().strftime('%Y-%m-%d'))),
            'salary_info': item.get('salary', item.get('salaryRange', None)),
            'employment_type': item.get('workType', item.get('job_type', None)),
            'experience_level': None,
            'applicants_count': None
        }
        jobs.append(job_data)
    
    print(f"✅ Found {len(jobs)} Seek jobs")
    return jobs


def fetch_job_from_url_apify(url: str) -> Optional[Dict]:
    """
    Fetch a single job from URL using Apify scrapers.
    This is for when users paste individual job URLs.
    """
    if not APIFY_API_KEY:
        print("Error: APIFY_API_KEY not found in environment")
        return None
    
    client = ApifyClient(APIFY_API_KEY)
    
    try:
        if 'linkedin.com' in url:
            return fetch_single_linkedin_job(client, url)
        elif 'seek.co.nz' in url:
            return fetch_single_seek_job(client, url)
        else:
            print(f"Unsupported platform for URL: {url}")
            return None
            
    except Exception as e:
        print(f"Error fetching job from {url}: {e}")
        return None


def fetch_single_linkedin_job(client: ApifyClient, url: str) -> Optional[Dict]:
    """Fetch a single LinkedIn job from URL."""
    try:
        run_input = {
            "startUrls": [{"url": url}],
            "maxItems": 1
        }
        
        run = client.actor("bebity/linkedin-jobs-scraper").call(run_input=run_input)
        
        if not run or "defaultDatasetId" not in run:
            return None
        
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            return {
                'job_title': item.get('job_title', item.get('title', 'LinkedIn Job')),
                'company_name': item.get('company', item.get('company_name', 'Unknown Company')),
                'location': item.get('location', ''),
                'description': item.get('description', item.get('job_description', ''))[:1000],
                'job_url': url,
                'source_platform': 'LinkedIn',
                'posted_date': item.get('posted_date', datetime.now().strftime('%Y-%m-%d')),
                'salary_info': item.get('salary', item.get('compensation', None)),
                'employment_type': item.get('employment_type', None),
                'experience_level': item.get('experience_level', None)
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching LinkedIn job: {e}")
        return None


def fetch_single_seek_job(client: ApifyClient, url: str) -> Optional[Dict]:
    """Fetch a single Seek job from URL."""
    try:
        job_id = url.split('/')[-1].split('?')[0]
        
        run_input = {
            "startUrls": [url],
            "maxItems": 1
        }
        
        run = client.actor("websift/seek-job-scraper").call(run_input=run_input)
        
        if not run or "defaultDatasetId" not in run:
            return None
        
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            return {
                'job_title': item.get('title', 'Seek Job'),
                'company_name': item.get('company', item.get('advertiser', 'Unknown Company')),
                'location': item.get('location', item.get('suburb', '')),
                'description': item.get('description', item.get('teaser', ''))[:1000],
                'job_url': url,
                'source_platform': 'Seek NZ',
                'posted_date': item.get('listedDate', datetime.now().strftime('%Y-%m-%d')),
                'salary_info': item.get('salary', item.get('salaryRange', None)),
                'employment_type': item.get('workType', None)
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching Seek job: {e}")
        return None
