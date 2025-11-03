import os
import base64
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email_parser import parse_job_alert_email
from database import insert_job, email_processed, mark_email_processed
from ai_matcher import analyze_job_match, should_analyze_job

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {CREDENTIALS_PATH}. "
                    "Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def decode_email_body(payload: Dict) -> str:
    """Decode email body from Gmail API response."""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html' or part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif 'parts' in part:
                for subpart in part['parts']:
                    if subpart['mimeType'] == 'text/html' or subpart['mimeType'] == 'text/plain':
                        if 'data' in subpart['body']:
                            body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                            break
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    
    return body

def get_email_headers(headers: List[Dict]) -> Dict[str, str]:
    """Extract important headers from email."""
    header_dict = {}
    for header in headers:
        name = header['name']
        if name in ['From', 'Subject', 'Date']:
            header_dict[name] = header['value']
    return header_dict

def fetch_job_alert_emails(service, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch job alert emails from LinkedIn and Seek NZ.
    Returns list of email data.
    """
    queries = [
        'from:linkedin.com OR from:jobs-listings@linkedin.com subject:(job alert OR recommended)',
        'from:seek.co.nz subject:(job alert OR job recommendation)'
    ]
    
    all_emails = []
    
    for query in queries:
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                msg_id = message['id']
                
                if email_processed(msg_id):
                    continue
                
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                
                headers = get_email_headers(msg['payload']['headers'])
                body = decode_email_body(msg['payload'])
                
                all_emails.append({
                    'id': msg_id,
                    'from': headers.get('From', ''),
                    'subject': headers.get('Subject', ''),
                    'body': body,
                    'date': headers.get('Date', '')
                })
                
        except Exception as e:
            print(f"Error fetching emails for query '{query}': {e}")
    
    return all_emails

def process_job_emails():
    """Main function to process job alert emails."""
    try:
        service = get_gmail_service()
        print("Connected to Gmail successfully")
        
        emails = fetch_job_alert_emails(service)
        print(f"Found {len(emails)} unprocessed job alert emails")
        
        total_jobs = 0
        auto_rejected = 0
        
        for email in emails:
            jobs = parse_job_alert_email(
                email['from'],
                email['subject'],
                email['body'],
                email['id']
            )
            
            for job in jobs:
                if should_analyze_job(job):
                    print(f"  🤖 Analyzing with AI: {job['job_title']}")
                    ai_result = analyze_job_match(job)
                    job['match_score'] = ai_result['match_score']
                    job['ai_analysis'] = ai_result['analysis']
                
                job_id = insert_job(job)
                if job_id:
                    total_jobs += 1
                    if job['status'] == 'auto-rejected':
                        auto_rejected += 1
                        print(f"  ❌ Auto-rejected: {job['job_title']} - {job['rejection_reason']}")
                    else:
                        score = job.get('match_score', 0)
                        print(f"  ✅ Added: {job['job_title']} at {job['company_name']} (Match: {score}%)")
            
            mark_email_processed(email['id'])
        
        print(f"\n📊 Summary:")
        print(f"   Total jobs found: {total_jobs}")
        print(f"   Auto-rejected (sponsorship): {auto_rejected}")
        print(f"   Ready for review: {total_jobs - auto_rejected}")
        
        return {
            'success': True,
            'total_jobs': total_jobs,
            'auto_rejected': auto_rejected
        }
        
    except Exception as e:
        print(f"Error processing job emails: {e}")
        return {
            'success': False,
            'error': str(e)
        }
