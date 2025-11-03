import os
from anthropic import Anthropic
from cv_profile import CV_SUMMARY, JOB_PREFERENCES

def analyze_job_match(job_data: dict) -> dict:
    """
    Use Claude AI to analyze a job posting and return match score and reasoning.
    
    Returns:
        dict with 'match_score' (0-100) and 'analysis' (reasoning)
    """
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not set, skipping AI analysis")
            return {'match_score': 0, 'analysis': 'AI analysis disabled - no API key'}
        
        client = Anthropic(api_key=api_key)
        
        job_title = job_data.get('job_title', '')
        company = job_data.get('company_name', '')
        location = job_data.get('location', '')
        description = job_data.get('description', '')
        salary = job_data.get('salary_info', 'Not specified')
        source = job_data.get('source_platform', '')
        
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
            model="claude-3-5-sonnet-latest",
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
                'analysis': 'AI response parsing error - no text content found'
            }
        
        score = 0
        analysis = response_text
        
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score_str = line.replace('SCORE:', '').strip()
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
        
        return {
            'match_score': score,
            'analysis': analysis
        }
        
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {
            'match_score': 0,
            'analysis': f'AI analysis error: {str(e)}'
        }

def should_analyze_job(job_data: dict) -> bool:
    """
    Check if a job should be analyzed by AI.
    Skip auto-rejected jobs.
    """
    if job_data.get('status') == 'auto-rejected':
        return False
    return True
