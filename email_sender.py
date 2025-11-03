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
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import Dict, Optional

def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = Credentials.from_authorized_user_file('token.json', 
        ['https://www.googleapis.com/auth/gmail.send'])
    return build('gmail', 'v1', credentials=creds)

def create_email_with_attachment(to: str, subject: str, body: str, attachment_path: Optional[str] = None) -> Dict:
    """
    Create an email message with optional attachment.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_path: Path to attachment file (optional)
    
    Returns:
        Dictionary with 'raw' email ready to send
    """
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    
    # Add body
    message.attach(MIMEText(body, 'plain'))
    
    # Add attachment if provided
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(attachment_path)}'
            )
            message.attach(part)
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_email_via_gmail(to: str, subject: str, body: str, attachment_path: Optional[str] = None) -> bool:
    """
    Send an email via Gmail API.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_path: Path to CV file (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        service = get_gmail_service()
        message = create_email_with_attachment(to, subject, body, attachment_path)
        
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
    Send a complete job application via Gmail.
    
    Args:
        recipient_email: Email address to send application to
        application: Dictionary with application details
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not recipient_email:
        print(f"   ⚠️  No recipient email - cannot send application")
        return False
    
    subject = application['email_subject']
    body = application['email_body']
    cv_path = application.get('cv_path')
    
    print(f"   📧 Sending application to: {recipient_email}")
    print(f"   📎 Subject: {subject}")
    
    # Send email with CV attachment
    success = send_email_via_gmail(
        to=recipient_email,
        subject=subject,
        body=body,
        attachment_path=cv_path if cv_path and os.path.exists(cv_path) else None
    )
    
    return success
