import os
import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from cv_profile import CV_SUMMARY, JOB_PREFERENCES

def fetch_job_description(url: str) -> str:
    """
    Fetch job description from the job posting URL.
    Returns the extracted description text or empty string if failed.
    """
    if not url:
        return ''
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"   Failed to fetch URL (status {response.status_code})")
            return ''
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()
        
        description_selectors = [
            '.job-description', '.description', '#job-description',
            '[class*="description"]', '[class*="job-detail"]',
            '.vacancy-description', '.job-content', '.posting-content',
            'article', 'main', '.content'
        ]
        
        description_text = ''
        for selector in description_selectors:
            elements = soup.select(selector)
            if elements:
                description_text = ' '.join([el.get_text(separator=' ', strip=True) for el in elements])
                if len(description_text) > 100:
                    break
        
        if len(description_text) < 100:
            body = soup.find('body')
            if body:
                description_text = body.get_text(separator=' ', strip=True)
        
        description_text = ' '.join(description_text.split())
        
        if len(description_text) > 5000:
            description_text = description_text[:5000] + '...'
        
        print(f"   ✅ Fetched description: {len(description_text)} chars")
        return description_text
        
    except Exception as e:
        print(f"   ❌ Error fetching description: {e}")
        return ''

def analyze_job_match(job_data: dict) -> dict:
    """
    Use Claude AI to analyze a job posting and return match score and reasoning.
    If description is missing, attempts to fetch it from the job URL.
    
    Returns:
        dict with 'match_score' (0-100), 'analysis' (reasoning), 'has_description' (bool), 
        and optionally 'fetched_description' if we retrieved it
    """
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not set, skipping AI analysis")
            return {'match_score': 0, 'analysis': 'AI analysis disabled - no API key', 'has_description': False}
        
        client = Anthropic(api_key=api_key)
        
        job_title = job_data.get('job_title', '')
        company = job_data.get('company_name', '')
        location = job_data.get('location', '')
        description = job_data.get('description', '')
        salary = job_data.get('salary_info', 'Not specified')
        source = job_data.get('source_platform', '')
        job_url = job_data.get('job_url', '')
        
        fetched_description = None
        description_missing = not description or len(description.strip()) < 50
        
        if description_missing and job_url:
            print(f"📥 Job '{job_title}' missing description - fetching from URL...")
            fetched_description = fetch_job_description(job_url)
            if fetched_description and len(fetched_description) >= 50:
                description = fetched_description
                description_missing = False
        
        if description_missing:
            print(f"⚠️ Job '{job_title}' at {company}: No description available (URL fetch failed or no URL)")
        
        prompt = f"""You are a career matching expert analyzing job postings for a highly experienced teacher.

CANDIDATE PROFILE:
{CV_SUMMARY}

JOB POSTING TO ANALYZE:
Title: {job_title}
Company: {company}
Location: {location}
Source: {source}
Salary: {salary}
Description: {description}

SCORING CRITERIA:
1. Location Match (0-30 points): Is this in New Zealand? (Critical requirement)
2. Role Match (0-30 points): Foundation Phase/Primary/Special Education teaching?
3. Experience Level (0-20 points): Suitable for 18+ years experience?
4. Specialization Match (0-20 points): Special needs, learning support, inclusive education?

IMPORTANT FILTERING:
- If NOT in New Zealand: Maximum score is 30
- If requires visa sponsorship: Automatic rejection (score 0)
- If the location clearly indicates it's NOT in New Zealand (e.g., Australia, UK, USA, South Africa): Score heavily penalized

Please provide:
1. A match score from 0-100
2. Brief analysis (2-3 sentences) explaining the score

Focus on whether this job is actually in NEW ZEALAND and suitable for this candidate's profile.

Format your response as:
SCORE: [number 0-100]
ANALYSIS: [your 2-3 sentence analysis]"""

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=300,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = None
        for block in message.content:
            if hasattr(block, 'text'):
                response_text = block.text
                break
        
        if not response_text:
            print(f"Warning: No text content found in AI response for '{job_title}'")
            return {
                'match_score': 0,
                'analysis': 'AI response parsing error - no text content found',
                'has_description': True
            }
        
        score = 0
        analysis = response_text
        
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score_str = line.replace('SCORE:', '').strip()
                    # Handle formats like "95/100" or "95"
                    if '/' in score_str:
                        score_str = score_str.split('/')[0].strip()
                    score = int(score_str)
                    print(f"Extracted score: {score}")
                except Exception as e:
                    print(f"Warning: Failed to parse score from line '{line}': {e}")
                    score = 0
            elif line.startswith('ANALYSIS:'):
                analysis = line.replace('ANALYSIS:', '').strip()
        
        if score == 0 and 'SCORE:' not in response_text:
            print(f"Warning: No valid SCORE found in AI response for '{job_title}'")
            print(f"Response preview: {response_text[:200]}")
        
        score = max(0, min(100, score))
        
        print(f"AI Analysis for '{job_title}': Score {score}/100")
        
        result = {
            'match_score': score,
            'analysis': analysis,
            'has_description': not description_missing
        }
        
        if fetched_description:
            result['fetched_description'] = fetched_description
            print(f"   📝 Returning fetched description for storage ({len(fetched_description)} chars)")
        
        return result
        
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {
            'match_score': 0,
            'analysis': f'AI analysis error: {str(e)}',
            'has_description': False
        }

def should_analyze_job(job_data: dict) -> bool:
    """
    Check if a job should be analyzed by AI.
    Skip auto-rejected jobs.
    """
    if job_data.get('status') == 'auto-rejected':
        return False
    return True
