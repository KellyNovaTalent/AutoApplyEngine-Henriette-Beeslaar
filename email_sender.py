"""
Email sender using Gmail API for automatic job applications.
Sends applications with CV and cover letter attachments.
"""
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from gmail_service import get_gmail_service

def create_email_with_attachments(to: str, subject: str, body: str, attachment_paths: Optional[List[str]] = None) -> Dict:
    """
    Create an email message with multiple attachments.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_paths: List of paths to attachment files (optional)
    
    Returns:
        Dictionary with 'raw' email ready to send
    """
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    
    # Add body
    message.attach(MIMEText(body, 'plain'))
    
    # Add all attachments
    if attachment_paths:
        for attachment_path in attachment_paths:
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(attachment_path)}'
                    )
                    message.attach(part)
                print(f"   📎 Attached: {os.path.basename(attachment_path)}")
            else:
                print(f"   ⚠️  Attachment not found: {attachment_path}")
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_email_via_gmail(to: str, subject: str, body: str, attachment_paths: Optional[List[str]] = None) -> bool:
    """
    Send an email via Gmail API with multiple attachments.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_paths: List of paths to attachment files (CV, cover letter, etc.)
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        service = get_gmail_service()
        message = create_email_with_attachments(to, subject, body, attachment_paths or [])
        
        result = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        print(f"   ✅ Email sent successfully! Message ID: {result['id']}")
        return True
        
    except FileNotFoundError:
        print(f"   ⚠️  Gmail not authenticated - run authentication first")
        return False
    except Exception as e:
        print(f"   ❌ Failed to send email: {e}")
        return False

def send_job_application(recipient_email: str, application: Dict) -> bool:
    """
    Send a complete job application via Gmail with CV and cover letter.
    
    Args:
        recipient_email: Email address to send application to
        application: Dictionary with application details including:
            - email_subject: Email subject line
            - email_body: Email body text
            - cv_path: Path to CV PDF
            - cover_letter_path: Path to cover letter PDF
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not recipient_email:
        print(f"   ⚠️  No recipient email - cannot send application")
        return False
    
    subject = application['email_subject']
    body = application['email_body']
    
    # Collect all attachments
    attachments = []
    
    if application.get('cv_path') and os.path.exists(application['cv_path']):
        attachments.append(application['cv_path'])
    
    if application.get('cover_letter_path') and os.path.exists(application['cover_letter_path']):
        attachments.append(application['cover_letter_path'])
    
    if not attachments:
        print(f"   ⚠️  No attachments found (CV or cover letter)")
    
    print(f"   📧 Sending application to: {recipient_email}")
    print(f"   📎 Subject: {subject}")
    print(f"   📄 Attachments: {len(attachments)}")
    
    # Send email with all attachments
    success = send_email_via_gmail(
        to=recipient_email,
        subject=subject,
        body=body,
        attachment_paths=attachments
    )
    
    return success
