import os
import base64
import requests
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_replit_gmail_access_token():
    """
    Get Gmail access token from Replit connection.
    Uses Replit's Gmail integration instead of manual OAuth.
    """
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    x_replit_token = None
    
    if os.environ.get('REPL_IDENTITY'):
        x_replit_token = 'repl ' + os.environ['REPL_IDENTITY']
    elif os.environ.get('WEB_REPL_RENEWAL'):
        x_replit_token = 'depl ' + os.environ['WEB_REPL_RENEWAL']
    
    if not x_replit_token or not hostname:
        raise Exception('Replit connection environment variables not found')
    
    # Fetch connection settings from Replit Connectors API
    response = requests.get(
        f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-mail',
        headers={
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
    )
    
    if not response.ok:
        raise Exception(f'Failed to get Gmail connection: {response.status_code}')
    
    data = response.json()
    connection = data.get('items', [{}])[0]
    
    # Extract access token
    access_token = (
        connection.get('settings', {}).get('access_token') or
        connection.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
    )
    
    if not access_token:
        raise Exception('Gmail not connected via Replit. Please set up the Gmail connector.')
    
    return access_token

def get_gmail_service():
    """Authenticate and return Gmail API service using Replit connection."""
    access_token = get_replit_gmail_access_token()
    
    # Create credentials object with access token
    creds = Credentials(token=access_token)
    
    return build('gmail', 'v1', credentials=creds)

def complete_auth_with_code(auth_code):
    """
    Deprecated: Old OAuth flow function - kept as stub for backward compatibility.
    Now using Replit Gmail connection instead.
    """
    raise Exception("Manual OAuth flow deprecated - using Replit Gmail connection instead")

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
    """
    Email processing feature (deprecated - now using Apify automation).
    Kept as stub for backward compatibility.
    """
    print("ℹ️  Email processing disabled - using Apify automated search instead")
    return {
        'success': True,
        'total_jobs': 0,
        'auto_rejected': 0,
        'message': 'Email processing disabled - using Apify automation'
    }
