"""
AI-powered cover letter generator using Claude.
Creates personalized cover letters tailored to each job posting.
"""
import os
from datetime import datetime
from anthropic import Anthropic
from cv_profile import USER_PROFILE

def generate_cover_letter(job_data: dict) -> str:
    """
    Generate a personalized cover letter for a job using Claude AI.
    
    Args:
        job_data: Dictionary containing job details (title, company, description, etc.)
    
    Returns:
        Professionally formatted cover letter as a string
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    client = Anthropic(api_key=api_key)
    user_profile = USER_PROFILE
    
    # Get current date formatted for NZ business letter
    current_date = datetime.now().strftime("%d %B %Y")
    
    prompt = f"""You are writing a professional cover letter for a teaching job application in New Zealand.

**Today's Date:** {current_date}

**Applicant Profile:**
Name: {user_profile['name']}
Email: {user_profile['email']}
Experience: {user_profile['experience_years']}+ years in {user_profile['specialization']}
Qualifications: {', '.join(user_profile['qualifications'])}
Key Skills: {', '.join(user_profile['key_skills'])}
Languages: {', '.join(user_profile['languages'])}

**Job Details:**
Position: {job_data['job_title']}
Company/School: {job_data['company_name']}
Location: {job_data.get('location', 'New Zealand')}
Description: {(job_data.get('description') or 'Teaching position in New Zealand school')[:1500]}

**Requirements:**
1. Write a compelling, professional cover letter (250-350 words)
2. Start with the date "{current_date}" at the top
3. Include a greeting (Dear Hiring Manager / Dear Principal)
4. Highlight relevant experience with special needs students (autism, Down syndrome, ADHD, intellectual disabilities)
5. Emphasize 18+ years of Foundation Phase and Special Education teaching experience
6. Mention NZ Teaching Registration and B.Ed Foundation Phase qualification
7. Show enthusiasm for the specific role and school
8. Include that I am currently based in South Africa and available to relocate within 6 weeks notice
9. Mention I am working with a licensed immigration advisor
10. Keep tone professional but warm and personable
11. End with ONLY ONE sign-off: "Warm regards," followed by a line break, then the name "{user_profile['name']}"
12. Do NOT add any postscripts, additional signatures, or extra contact information
13. Do NOT repeat the signature or name multiple times

Write only the complete cover letter, nothing else:"""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Extract text from response
    cover_letter = ""
    for block in response.content:
        if block.type == 'text':
            cover_letter = block.text.strip()
            break
    
    if not cover_letter:
        cover_letter = str(response.content)
    
    print(f"✍️  Generated cover letter ({len(cover_letter)} chars)")
    return cover_letter


def generate_email_subject(job_data: dict) -> str:
    """Generate a professional email subject line for the job application."""
    return f"Application for {job_data['job_title']} - {USER_PROFILE['name']}"


def generate_email_body(job_data: dict, cover_letter: str) -> str:
    """
    Generate the email body for a job application.
    Uses the cover letter as the main body (it already has proper greeting and signature).
    The cover letter is self-contained and complete.
    """
    return cover_letter.strip()
