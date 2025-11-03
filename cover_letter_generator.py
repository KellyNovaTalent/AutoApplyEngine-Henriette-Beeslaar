"""
AI-powered cover letter generator using Claude.
Creates personalized cover letters tailored to each job posting.
"""
import os
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
    
    prompt = f"""You are writing a professional cover letter for a teaching job application in New Zealand.

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
Location: {job_data['location']}
Description: {job_data['description'][:1500]}

**Requirements:**
1. Write a compelling, professional cover letter (250-350 words)
2. Highlight relevant experience with special needs students (autism, Down syndrome, ADHD, intellectual disabilities)
3. Emphasize 18+ years of Foundation Phase and Special Education teaching experience
4. Mention NZ Teaching Registration and B.Ed Foundation Phase qualification
5. Show enthusiasm for the specific role and school
6. Keep tone professional but warm and personable
7. Include proper New Zealand business letter format
8. Do NOT include placeholder addresses - start directly with the greeting
9. Sign off with "Warm regards" or "Kind regards"

Write the complete cover letter now:"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Extract text from response
    for block in response.content:
        if hasattr(block, 'text'):
            cover_letter = block.text.strip()
            break
    else:
        cover_letter = str(response.content[0])
    
    print(f"✍️  Generated cover letter ({len(cover_letter)} chars)")
    return cover_letter


def generate_email_subject(job_data: dict) -> str:
    """Generate a professional email subject line for the job application."""
    return f"Application for {job_data['job_title']} - {USER_PROFILE['name']}"


def generate_email_body(job_data: dict, cover_letter: str) -> str:
    """
    Generate the email body for a job application.
    Includes a brief introduction and the cover letter.
    """
    user_profile = USER_PROFILE
    
    email_body = f"""Dear Hiring Manager,

Please find attached my application for the {job_data['job_title']} position at {job_data['company_name']}.

{cover_letter}

I have attached my CV for your review. I would welcome the opportunity to discuss how my experience and skills align with your school's needs.

Thank you for considering my application.

Warm regards,
{user_profile['name']}
{user_profile['email']}
{user_profile.get('phone', '')}
"""
    
    return email_body.strip()
