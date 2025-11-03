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

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'

def complete_auth_with_code(auth_code):
    """Complete the OAuth flow with the authorization code."""
    if not os.path.exists(CREDENTIALS_PATH):
        raise Exception("Credentials file not found")
    
    # Create a new flow instance
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    
    # Fetch the token using the authorization code
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    
    # Save credentials
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())
    
    return True

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
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            raise Exception(f"AUTHORIZATION_REQUIRED|||{auth_url}")
        
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

def test_gmail_connection(service):
    """Test basic Gmail API connectivity and show what emails exist."""
    print("\n" + "="*80)
    print("🔍 GMAIL API CONNECTION TEST")
    print("="*80)
    
    try:
        # Test 1: Get total inbox count
        print("\n1️⃣ Testing basic Gmail API access...")
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        print(f"✅ Gmail API is working! Connection successful.")
        
        # Test 2: Show last 20 emails from inbox
        print("\n2️⃣ Fetching last 20 emails from inbox...")
        results = service.users().messages().list(userId='me', maxResults=20).execute()
        messages = results.get('messages', [])
        print(f"📬 Found {len(messages)} recent emails in inbox")
        
        if messages:
            print("\n📧 Recent emails:")
            for i, msg in enumerate(messages[:10], 1):
                full_msg = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
                headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
                print(f"\n   {i}. From: {headers.get('From', 'Unknown')[:60]}")
                print(f"      Subject: {headers.get('Subject', 'No subject')[:60]}")
                print(f"      Date: {headers.get('Date', 'Unknown')[:40]}")
        
        # Test 3: Search for ANY job-related emails
        print("\n3️⃣ Searching for job-related keywords...")
        test_queries = [
            'subject:job',
            'subject:teacher',
            'subject:vacancy',
            'subject:LinkedIn',
            'subject:SEEK'
        ]
        
        for query in test_queries:
            results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            count = len(results.get('messages', []))
            print(f"   '{query}' → Found {count} emails")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Gmail API Error: {e}")
        raise

def fetch_job_alert_emails(service, max_results: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch job alert emails with FLEXIBLE detection from the last X days.
    Searches across ALL Gmail tabs (Primary, Promotions, Updates) using broad queries.
    """
    from datetime import datetime, timedelta
    
    # Run connection test first
    test_gmail_connection(service)
    
    # Calculate date filter (last 30 days)
    date_filter = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    
    print("\n" + "="*80)
    print("🔎 SEARCHING FOR JOB EMAILS")
    print("="*80)
    print(f"Date filter: After {date_filter} (last {days_back} days)")
    
    # SIMPLIFIED queries - just search for keywords
    queries = [
        f'subject:"LinkedIn Job" after:{date_filter}',
        f'subject:SEEK after:{date_filter}',
        f'from:education.govt.nz after:{date_filter}',
        f'subject:job after:{date_filter}',
        f'subject:teacher after:{date_filter}',
    ]
    
    all_emails = []
    seen_ids = set()
    
    for i, query in enumerate(queries, 1):
        try:
            print(f"\n{i}. Query: {query}")
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            print(f"   ✅ Found: {len(messages)} emails")
            
            for message in messages:
                msg_id = message['id']
                
                # Skip duplicates
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)
                
                # Process ALL emails
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                
                headers = get_email_headers(msg['payload']['headers'])
                body = decode_email_body(msg['payload'])
                
                email_from = headers.get('From', '')
                email_subject = headers.get('Subject', '')
                
                # Log what we found
                print(f"  📧 From: {email_from[:60]}")
                print(f"      Subject: {email_subject[:60]}")
                
                all_emails.append({
                    'id': msg_id,
                    'from': email_from,
                    'subject': email_subject,
                    'body': body,
                    'date': headers.get('Date', '')
                })
                
        except Exception as e:
            print(f"❌ Error fetching emails for query: {e}")
    
    print(f"\n✅ Total unique emails found: {len(all_emails)}")
    return all_emails

def process_job_emails():
    """Main function to process job alert emails."""
    try:
        service = get_gmail_service()
        print("Connected to Gmail successfully")
        
        emails = fetch_job_alert_emails(service)
        print(f"Found {len(emails)} job alert emails from the last 30 days")
        
        total_jobs = 0
        auto_rejected = 0
        
        for email in emails:
            print(f"\n{'='*60}")
            jobs = parse_job_alert_email(
                email['from'],
                email['subject'],
                email['body'],
                email['id']
            )
            
            if not jobs:
                print(f"   ⚠️ No jobs extracted from this email")
            
            for job in jobs:
                if should_analyze_job(job):
                    print(f"  🤖 Analyzing with AI: {job['job_title']}")
                    ai_result = analyze_job_match(job)
                    job['match_score'] = ai_result['match_score']
                    job['ai_analysis'] = ai_result['analysis']
                
                # Try to insert job (database will handle duplicates)
                job_id = insert_job(job)
                if job_id:
                    total_jobs += 1
                    if job['status'] == 'auto-rejected':
                        auto_rejected += 1
                        print(f"  ❌ Auto-rejected: {job['job_title']} - {job['rejection_reason']}")
                    else:
                        score = job.get('match_score', 0)
                        print(f"  ✅ Added: {job['job_title']} at {job['company_name']} (Match: {score}%)")
                else:
                    print(f"  ⏭️  Skipped duplicate: {job['job_title']}")
            
            # Mark email as processed
            if not email_processed(email['id']):
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
