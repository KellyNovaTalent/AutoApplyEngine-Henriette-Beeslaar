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
1. Write ONLY a professional cover letter (250-350 words)
2. Format: Date → Greeting → Body paragraphs → Closing signature
3. Start with: {current_date}
4. Include greeting: Dear Hiring Manager (or Dear Principal/Headmaster)
5. Body: Highlight special needs experience (autism, Down syndrome, ADHD)
6. Emphasize 18+ years Foundation Phase & Special Education background
7. Mention NZ Teaching Registration and B.Ed Foundation Phase
8. State: "I am currently based in South Africa and available to relocate within 6 weeks notice"
9. State: "I am working with a licensed immigration advisor for a smooth transition to New Zealand"
10. Professional but warm tone
11. CRITICAL: End with EXACTLY this format:
    Warm regards,
    Henriëtte Charlotte Beeslaar

12. DO NOT add anything after "Henriëtte Charlotte Beeslaar" - no email, no phone, no WhatsApp, no LinkedIn, no extra text
13. DO NOT include postscripts, attachments mentions, or any content beyond the signature
14. Output ONLY the cover letter text - nothing before or after

Generate the complete cover letter now:"""

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
    
    if cover_letter:
        lines = cover_letter.split('\n')
        final_lines = []
        signature_found = False
        
        for line in lines:
            final_lines.append(line)
            if user_profile['name'] in line:
                signature_found = True
                break
        
        if signature_found:
            cover_letter = '\n'.join(final_lines)
    
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
