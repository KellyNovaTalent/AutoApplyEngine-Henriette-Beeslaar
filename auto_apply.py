"""
Automatic job application system.
Sends applications with CV and tailored cover letters for matching jobs.
"""
import os
from datetime import datetime
from typing import Dict, Optional
from cover_letter_generator import generate_cover_letter, generate_email_subject, generate_email_body
from cover_letter_pdf import save_cover_letter_as_pdf
from cv_profile import USER_PROFILE
from database import update_job_status
from email_sender import send_job_application

# Auto-apply is now enabled by default with Gmail integration
AUTO_APPLY_ENABLED = os.environ.get('AUTO_APPLY_ENABLED', 'true').lower() == 'true'
MIN_MATCH_SCORE_FOR_AUTO_APPLY = 70


def should_auto_apply(job_data: dict) -> bool:
    """
    Determine if we should automatically apply to this job.
    
    Criteria:
    - Match score >= 70%
    - Status is 'new' (not already applied)
    - Auto-apply is enabled in config
    """
    match_score = job_data.get('match_score', 0)
    status = job_data.get('status', 'new')
    
    if status != 'new':
        return False
    
    if match_score < MIN_MATCH_SCORE_FOR_AUTO_APPLY:
        return False
    
    return True


def prepare_application(job_data: dict) -> Dict:
    """
    Prepare a complete job application.
    
    Returns:
        Dictionary containing:
        - cover_letter: Personalized cover letter text
        - email_subject: Email subject line
        - email_body: Complete email body
        - cv_path: Path to CV file
        - recipient_email: Where to send (if available)
    """
    print(f"\n📝 Preparing application for: {job_data['job_title']}")
    print(f"   Company: {job_data['company_name']}")
    print(f"   Match Score: {job_data.get('match_score', 0)}%")
    
    # Generate cover letter
    cover_letter = generate_cover_letter(job_data)
    
    # Save cover letter as PDF
    cover_letter_path = save_cover_letter_as_pdf(
        cover_letter,
        job_data['job_title'],
        job_data.get('company_name', 'Company')
    )
    
    # Generate email
    email_subject = generate_email_subject(job_data)
    email_body = generate_email_body(job_data, cover_letter)
    
    user_profile = USER_PROFILE
    
    application = {
        'job_id': job_data.get('id'),
        'job_title': job_data['job_title'],
        'company_name': job_data['company_name'],
        'cover_letter': cover_letter,
        'cover_letter_path': cover_letter_path,  # Path to cover letter PDF
        'email_subject': email_subject,
        'email_body': email_body,
        'cv_path': user_profile.get('cv_path', 'cv.pdf'),
        'recipient_email': extract_email_from_job(job_data),
        'prepared_at': datetime.now().isoformat()
    }
    
    return application


def extract_email_from_job(job_data: dict) -> Optional[str]:
    """
    Try to extract contact email from job description.
    Returns None if no email found.
    """
    import re
    description = job_data.get('description', '')
    
    # Look for email patterns
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, description)
    
    if emails:
        return emails[0]
    
    return None


def send_application(application: Dict) -> bool:
    """
    Send the job application via Gmail API.
    
    Returns:
        True if sent successfully, False if email missing or send failed
    """
    if not AUTO_APPLY_ENABLED:
        print(f"   ⏸️  Auto-apply disabled - application prepared but not sent")
        return False
    
    recipient = application.get('recipient_email')
    if not recipient:
        print(f"   ⚠️  No contact email found in job description")
        print(f"   📋 Cover letter generated - manual application required via job portal")
        print(f"   🔗 Apply manually at: {application.get('job_url', 'N/A')}")
        # Application is prepared but requires manual sending
        return False
    
    # Send via Gmail API
    try:
        success = send_job_application(recipient, application)
        return success
    except Exception as e:
        print(f"   ❌ Error sending application: {e}")
        return False


def auto_apply_to_job(job_data: dict) -> Dict:
    """
    Complete auto-apply workflow for a single job.
    
    Returns:
        Dictionary with application status and details
    """
    if not should_auto_apply(job_data):
        return {
            'success': False,
            'reason': f"Does not meet auto-apply criteria (score: {job_data.get('match_score', 0)}%)"
        }
    
    try:
        # Prepare application
        application = prepare_application(job_data)
        
        # Send application
        sent = send_application(application)
        
        # Update job status in database
        if job_data.get('id'):
            if sent:
                update_job_status(
                    job_data['id'],
                    'applied',
                    f"✅ Auto-sent via Gmail on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                # Application prepared but needs manual sending through job portal
                job_url = job_data.get('job_url', 'No URL')
                update_job_status(
                    job_data['id'],
                    'ready_to_apply',
                    f"📋 Cover letter ready! Apply manually at job portal: {job_url}"
                )
        
        return {
            'success': True,
            'sent': sent,
            'application': application
        }
        
    except Exception as e:
        print(f"   ❌ Error applying to job: {e}")
        return {
            'success': False,
            'error': str(e)
        }
