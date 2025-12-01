import os
import csv
from io import StringIO
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, get_all_jobs, get_job_stats, update_job_status, insert_job
from gmail_service import process_job_emails, complete_auth_with_code
from job_fetcher_apify import search_jobs_apify, fetch_job_from_url_apify
from job_fetcher_gazette import search_education_gazette
from ai_matcher import analyze_job_match
from job_search_config import USER_SEARCH_CONFIG, EXCLUDED_KEYWORDS
from apify_cost_tracker import can_make_search, can_fetch_jobs, record_search, get_usage_stats
from auto_apply import auto_apply_to_job, should_auto_apply
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set for secure session management")
if not AUTH_PASSWORD:
    raise ValueError("AUTH_PASSWORD environment variable must be set for authentication")

app = Flask(__name__)
app.secret_key = SECRET_KEY

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == AUTH_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    filters = {}
    
    source = request.args.get('source')
    if source and source != 'all':
        filters['source_platform'] = source
    
    status = request.args.get('status')
    if status and status != 'all':
        filters['status'] = status
    
    # Handle both min_score and min_match parameters
    min_score = request.args.get('min_score') or request.args.get('min_match')
    if min_score:
        filters['min_score'] = int(min_score)
    
    jobs = get_all_jobs(filters)
    stats = get_job_stats()
    
    return render_template('index.html', jobs=jobs, stats=stats, filters=request.args)

@app.route('/api/sync', methods=['POST'])
@login_required
def sync_emails():
    result = process_job_emails()
    
    # Check if authorization is required
    if not result.get('success') and 'AUTHORIZATION_REQUIRED|||' in result.get('error', ''):
        parts = result['error'].split('|||')
        if len(parts) == 2:
            auth_url = parts[1]
            print(f"Authorization required. URL: {auth_url}")
            return jsonify({
                'success': False,
                'error': 'authorization_required',
                'auth_url': auth_url
            })
    
    return jsonify(result)

@app.route('/api/auth/complete', methods=['POST'])
@login_required
def complete_authorization():
    data = request.get_json()
    auth_code = data.get('code')
    
    if not auth_code:
        return jsonify({'success': False, 'error': 'No authorization code provided'})
    
    try:
        print(f"Completing authorization with code: {auth_code[:20]}...")
        complete_auth_with_code(auth_code)
        print("Authorization successful, processing emails...")
        result = process_job_emails()
        return jsonify(result)
    except Exception as e:
        print(f"Authorization error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze_jobs', methods=['POST'])
@login_required
def analyze_jobs():
    """Analyze job URLs pasted by user."""
    try:
        data = request.get_json()
        urls_text = data.get('urls', '')
        
        # Parse URLs from text (one per line)
        import re
        urls = [line.strip() for line in urls_text.split('\n') if line.strip()]
        
        # Filter valid URLs
        valid_urls = [url for url in urls if url.startswith('http')]
        
        if not valid_urls:
            return jsonify({'success': False, 'error': 'No valid URLs provided'})
        
        print(f"\n{'='*80}")
        print(f"🔍 Analyzing {len(valid_urls)} job URLs")
        print(f"{'='*80}")
        
        jobs_analyzed = 0
        jobs_failed = 0
        
        for url in valid_urls:
            print(f"\n📋 Fetching: {url[:60]}...")
            
            # Fetch job data using Apify scraper
            job_data = fetch_job_from_url_apify(url)
            
            if not job_data:
                print(f"   ❌ Failed to fetch job")
                jobs_failed += 1
                continue
            
            print(f"   ✅ Fetched: {job_data['job_title']}")
            print(f"   🏢 Company: {job_data['company_name']}")
            
            # Analyze with AI
            print(f"   🤖 Analyzing with Claude AI...")
            ai_result = analyze_job_match(job_data)
            job_data['match_score'] = ai_result['match_score']
            job_data['ai_analysis'] = ai_result['analysis']
            job_data['status'] = 'new'
            job_data['rejection_reason'] = None
            job_data['email_id'] = None
            
            print(f"   ✨ Match Score: {ai_result['match_score']}%")
            
            # Insert into database
            job_id = insert_job(job_data)
            if job_id:
                jobs_analyzed += 1
                print(f"   💾 Saved to database (ID: {job_id})")
            else:
                print(f"   ⏭️  Duplicate job (already in database)")
                jobs_analyzed += 1  # Count as analyzed even if duplicate
        
        print(f"\n{'='*80}")
        print(f"✅ Analysis Complete!")
        print(f"   Analyzed: {jobs_analyzed}/{len(valid_urls)}")
        print(f"   Failed: {jobs_failed}/{len(valid_urls)}")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': True,
            'jobs_analyzed': jobs_analyzed,
            'jobs_failed': jobs_failed,
            'total_urls': len(valid_urls)
        })
        
    except Exception as e:
        print(f"❌ Error analyzing jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/auto_search_jobs', methods=['POST'])
@login_required
def auto_search_jobs():
    """JobCopilot-style automated job search using Apify."""
    try:
        print(f"\n{'='*80}")
        print(f"🚀 AUTOMATIC JOB SEARCH STARTED (JobCopilot Mode)")
        print(f"{'='*80}")
        
        # Check usage limits
        usage_stats = get_usage_stats()
        print(f"📊 Today's usage: {usage_stats['searches_today']} searches, {usage_stats['jobs_fetched_today']} jobs")
        
        if not can_make_search():
            return jsonify({
                'success': False,
                'error': 'Daily search limit reached',
                'usage': usage_stats
            })
        
        if not USER_SEARCH_CONFIG['enabled']:
            return jsonify({'success': False, 'error': 'Auto search is disabled'})
        
        all_jobs_found = []
        total_new_jobs = 0
        total_jobs_from_apify = 0
        jobs_fetched_this_run = 0
        
        # Determine which platforms to search
        platforms_to_search = USER_SEARCH_CONFIG.get('platforms', ['linkedin', 'seek'])
        if 'linkedin' in platforms_to_search and 'seek' in platforms_to_search:
            platform_mode = 'both'
        elif 'linkedin' in platforms_to_search:
            platform_mode = 'linkedin'
        elif 'seek' in platforms_to_search:
            platform_mode = 'seek'
        else:
            return jsonify({'success': False, 'error': 'No platforms configured'})
        
        # OPTIONAL: Search Education Gazette if enabled
        if 'education_gazette' in platforms_to_search:
            print(f"\n📰 Searching Education Gazette NZ...")
            try:
                gazette_jobs = search_education_gazette(max_jobs=20)
                for job_data in gazette_jobs:
                    job_text = f"{job_data['job_title']} {job_data['description']}".lower()
                    if any(excluded in job_text for excluded in EXCLUDED_KEYWORDS):
                        continue
                    
                    ai_result = analyze_job_match(job_data)
                    job_data['match_score'] = ai_result['match_score']
                    job_data['ai_analysis'] = ai_result['analysis']
                    job_data['status'] = 'new'
                    
                    job_id = insert_job(job_data)
                    if job_id:
                        job_data['id'] = job_id
                        total_new_jobs += 1
                        all_jobs_found.append(job_data)
                        
                        if should_auto_apply(job_data):
                            auto_apply_to_job(job_data)
            except Exception as e:
                print(f"   ⚠️  Education Gazette unavailable: {e}")
        
        # SEARCH LINKEDIN + SEEK (via Apify) - Main job sources
        for keyword in USER_SEARCH_CONFIG['keywords']:
            print(f"\n🔎 Searching LinkedIn/Seek for: {keyword}")
            
            # Calculate jobs to fetch for this keyword
            jobs_per_keyword = USER_SEARCH_CONFIG['max_jobs_per_search'] // len(USER_SEARCH_CONFIG['keywords'])
            
            # Check if we can fetch more jobs (including what we've fetched this run)
            if not can_fetch_jobs(jobs_per_keyword, jobs_fetched_this_run):
                print(f"⚠️  Daily job limit would be exceeded, stopping search")
                print(f"   Already fetched {jobs_fetched_this_run} jobs this run")
                break
            
            # Search using Apify
            jobs = search_jobs_apify(
                keywords=keyword,
                location=USER_SEARCH_CONFIG['location'],
                max_jobs=jobs_per_keyword,
                platform=platform_mode,
                remote_only=USER_SEARCH_CONFIG.get('remote_ok', False)
            )
            
            print(f"   Found {len(jobs)} jobs for '{keyword}'")
            total_jobs_from_apify += len(jobs)
            jobs_fetched_this_run += len(jobs)
            
            for job_data in jobs:
                # Filter out excluded keywords
                job_text = f"{job_data['job_title']} {job_data['description']}".lower()
                if any(excluded in job_text for excluded in EXCLUDED_KEYWORDS):
                    print(f"   ⏭️  Skipped: {job_data['job_title']} (contains excluded keyword)")
                    continue
                
                # Analyze with AI
                print(f"   🤖 Analyzing: {job_data['job_title']}")
                ai_result = analyze_job_match(job_data)
                job_data['match_score'] = ai_result['match_score']
                job_data['ai_analysis'] = ai_result['analysis']
                job_data['status'] = 'new'
                job_data['rejection_reason'] = None
                job_data['email_id'] = None
                
                print(f"   ✨ Match Score: {ai_result['match_score']}%")
                
                # Insert into database
                job_id = insert_job(job_data)
                if job_id:
                    job_data['id'] = job_id
                    total_new_jobs += 1
                    all_jobs_found.append(job_data)
                    print(f"   💾 Saved (ID: {job_id})")
                    
                    # Auto-apply if match score is high enough
                    if should_auto_apply(job_data):
                        print(f"   🎯 Match score {job_data['match_score']}% - attempting auto-apply")
                        apply_result = auto_apply_to_job(job_data)
                        if apply_result['success']:
                            print(f"   ✅ Application prepared")
                        else:
                            print(f"   ⏭️  Auto-apply skipped: {apply_result.get('reason', 'Unknown')}")
        
        # Record usage (only record once at the end)
        record_search(jobs_fetched_this_run)
        
        print(f"\n{'='*80}")
        print(f"✅ AUTO SEARCH COMPLETE!")
        print(f"   New jobs found: {total_new_jobs}")
        print(f"   Total fetched from Apify: {total_jobs_from_apify}")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': True,
            'jobs_found': total_new_jobs,
            'keywords_searched': len(USER_SEARCH_CONFIG['keywords']),
            'usage': get_usage_stats()
        })
        
    except Exception as e:
        print(f"❌ Error in auto search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/jobs/<int:job_id>/update', methods=['POST'])
@login_required
def update_job(job_id):
    data = request.get_json()
    status = data.get('status')
    notes = data.get('notes')
    
    update_job_status(job_id, status, notes)
    return jsonify({'success': True})

@app.route('/api/stats')
@login_required
def stats():
    return jsonify(get_job_stats())

@app.route('/scrape_education_gazette', methods=['POST'])
@login_required
def scrape_gazette_endpoint():
    """
    Trigger Education Gazette scraper directly from web interface.
    """
    try:
        print(f"\n{'='*80}")
        print(f"📰 EDUCATION GAZETTE DIRECT SCRAPE")
        print(f"{'='*80}")
        
        gazette_jobs = search_education_gazette(max_jobs=30)
        
        jobs_imported = 0
        jobs_skipped = 0
        
        for job_data in gazette_jobs:
            try:
                job_text = f"{job_data['job_title']} {job_data['description']}".lower()
                if any(excluded in job_text for excluded in EXCLUDED_KEYWORDS):
                    print(f"   ⏭️  Skipped: {job_data['job_title']} (excluded keyword)")
                    jobs_skipped += 1
                    continue
                
                print(f"   🤖 Analyzing: {job_data['job_title']}")
                ai_result = analyze_job_match(job_data)
                job_data['match_score'] = ai_result['match_score']
                job_data['ai_analysis'] = ai_result['analysis']
                job_data['status'] = 'new'
                
                print(f"   ✨ Match Score: {ai_result['match_score']}%")
                
                job_id = insert_job(job_data)
                if job_id:
                    jobs_imported += 1
                    print(f"   💾 Saved (ID: {job_id})")
                    
                    if should_auto_apply(job_data):
                        auto_apply_to_job(job_data)
                else:
                    jobs_skipped += 1
                    
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                jobs_skipped += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"✅ EDUCATION GAZETTE SCRAPE COMPLETE!")
        print(f"   Jobs imported: {jobs_imported}")
        print(f"{'='*80}\n")
        
        if jobs_imported == 0 and len(gazette_jobs) == 0:
            return jsonify({
                'success': False,
                'error': 'Education Gazette is currently blocking requests. Please use CSV upload instead.'
            })
        
        return jsonify({
            'success': True,
            'jobs_found': jobs_imported,
            'jobs_skipped': jobs_skipped
        })
        
    except Exception as e:
        print(f"❌ Error scraping Education Gazette: {e}")
        return jsonify({
            'success': False,
            'error': 'Education Gazette scraper blocked. Please use CSV upload option.'
        })

@app.route('/analyze_new_jobs', methods=['POST'])
@login_required
def analyze_new_jobs():
    """
    Analyze all jobs with status 'new' using AI and auto-apply to 70%+ matches.
    This is useful after adding a new API key or uploading new jobs.
    """
    try:
        import sqlite3
        
        print(f"\n{'='*80}")
        print(f"🤖 ANALYZING NEW JOBS & AUTO-APPLYING")
        print(f"{'='*80}")
        
        conn = sqlite3.connect('jobs.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all jobs with status 'new' that haven't been analyzed (match_score is 0 or NULL)
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE status = 'new' 
            AND (match_score IS NULL OR match_score = 0)
            ORDER BY id DESC
            LIMIT 100
        ''')
        new_jobs = cursor.fetchall()
        conn.close()
        
        total_jobs = len(new_jobs)
        jobs_analyzed = 0
        jobs_applied = 0
        jobs_failed = 0
        
        print(f"   Found {total_jobs} jobs to analyze")
        
        for row in new_jobs:
            job_data = dict(row)
            
            try:
                print(f"\n   🤖 Analyzing: {job_data['job_title'][:50]}...")
                
                # Analyze with AI
                ai_result = analyze_job_match(job_data)
                job_data['match_score'] = ai_result['match_score']
                job_data['ai_analysis'] = ai_result['analysis']
                
                print(f"   ✨ Match Score: {ai_result['match_score']}%")
                
                # Update the job in database with score
                conn = sqlite3.connect('jobs.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE jobs 
                    SET match_score = ?, ai_analysis = ?
                    WHERE id = ?
                ''', (ai_result['match_score'], ai_result['analysis'], job_data['id']))
                conn.commit()
                conn.close()
                
                jobs_analyzed += 1
                
                # Auto-apply if match score is 70% or higher
                if ai_result['match_score'] >= 70:
                    print(f"   🎯 High match - attempting auto-apply...")
                    apply_result = auto_apply_to_job(job_data)
                    if apply_result.get('success') and apply_result.get('sent'):
                        jobs_applied += 1
                        print(f"   ✅ Application sent!")
                    elif apply_result.get('success'):
                        print(f"   📋 Application prepared (no email found)")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
                jobs_failed += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"   Jobs analyzed: {jobs_analyzed}")
        print(f"   Applications sent: {jobs_applied}")
        print(f"   Failed: {jobs_failed}")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': True,
            'jobs_analyzed': jobs_analyzed,
            'jobs_applied': jobs_applied,
            'jobs_failed': jobs_failed,
            'total_jobs': total_jobs
        })
        
    except Exception as e:
        print(f"❌ Error analyzing jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload_gazette_csv', methods=['POST'])
@login_required
def upload_gazette_csv():
    """
    Universal CSV Upload - accepts Education Gazette OR Seek scraper formats.
    Auto-detects format and imports accordingly.
    
    Gazette format: Title, Employer, Description, Email, Link, Closing
    Seek format: Hiring Company, Position, Application Link, Email, Phone, Description
    """
    try:
        print(f"\n{'='*80}")
        print(f"📤 UNIVERSAL CSV UPLOAD")
        print(f"{'='*80}")
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV'})
        
        csv_content = file.read().decode('utf-8')
        
        # Auto-detect delimiter (comma or semicolon)
        first_line = csv_content.split('\n')[0]
        delimiter = ';' if ';' in first_line else ','
        print(f"   📋 Detected delimiter: '{delimiter}'")
        
        csv_reader = csv.DictReader(StringIO(csv_content), delimiter=delimiter)
        
        rows = list(csv_reader)
        if not rows:
            return jsonify({'success': False, 'error': 'CSV file is empty'})
        
        first_row = rows[0]
        print(f"   📋 CSV columns: {list(first_row.keys())}")
        
        is_seek_format = 'Hiring Company' in first_row and 'Position' in first_row
        is_gazette_format = 'Title' in first_row and 'Employer' in first_row
        
        if is_seek_format:
            print("   📋 Detected: Seek CSV format")
            source_platform = 'Seek NZ (CSV Upload)'
        elif is_gazette_format:
            print("   📋 Detected: Education Gazette CSV format")
            source_platform = 'Education Gazette NZ (CSV Upload)'
        else:
            return jsonify({'success': False, 'error': 'Unrecognized CSV format. Expected Education Gazette or Seek format.'})
        
        jobs_imported = 0
        jobs_skipped = 0
        
        for row in rows:
            try:
                if is_seek_format:
                    job_title = row.get('Position', '')
                    company_name = row.get('Hiring Company', '')
                    job_url = row.get('Application Link', '')
                    description = row.get('Description', '')
                    contact_email = row.get('Email', None)
                    phone = row.get('Phone', '')
                else:
                    job_title = row.get('Title', '')
                    company_name = row.get('Employer', 'NZ School')
                    job_url = row.get('Link', '')
                    description = row.get('Description', '')
                    contact_email = row.get('Email', None)
                    phone = ''
                
                if not job_title or not job_url:
                    jobs_skipped += 1
                    continue
                
                if contact_email == 'N/A' or not contact_email:
                    contact_email = None
                
                job_data = {
                    'job_title': job_title,
                    'company_name': company_name,
                    'location': extract_location_from_description(description),
                    'job_url': job_url,
                    'description': description[:2000],
                    'posted_date': row.get('Closing', row.get('Posted', '')),
                    'source_platform': source_platform,
                    'salary_info': None,
                    'contact_email': contact_email
                }
                
                job_text = f"{job_title} {description}".lower()
                if any(excluded in job_text for excluded in EXCLUDED_KEYWORDS):
                    print(f"   ⏭️  Skipped: {job_title} (contains excluded keyword)")
                    jobs_skipped += 1
                    continue
                
                print(f"   🤖 Analyzing: {job_title}")
                ai_result = analyze_job_match(job_data)
                job_data['match_score'] = ai_result['match_score']
                job_data['ai_analysis'] = ai_result['analysis']
                job_data['status'] = 'new'
                
                print(f"   ✨ Match Score: {ai_result['match_score']}%")
                if contact_email:
                    print(f"   📧 Email: {contact_email}")
                
                job_id = insert_job(job_data)
                if job_id:
                    job_data['id'] = job_id
                    jobs_imported += 1
                    print(f"   💾 Saved (ID: {job_id})")
                    
                    if should_auto_apply(job_data):
                        print(f"   🎯 Match score {job_data['match_score']}% - attempting auto-apply")
                        apply_result = auto_apply_to_job(job_data)
                        if apply_result['success']:
                            print(f"   ✅ Application prepared")
                        else:
                            print(f"   ⏭️  Auto-apply skipped: {apply_result.get('reason', '')}")
                else:
                    jobs_skipped += 1
                
            except Exception as e:
                print(f"   ⚠️  Error processing row: {e}")
                jobs_skipped += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"✅ CSV IMPORT COMPLETE!")
        print(f"   Jobs imported: {jobs_imported}")
        print(f"   Jobs skipped: {jobs_skipped}")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': True,
            'jobs_imported': jobs_imported,
            'jobs_skipped': jobs_skipped
        })
        
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

def extract_location_from_description(description: str) -> str:
    """Extract location from job description."""
    locations = [
        'Auckland', 'Wellington', 'Canterbury', 'Christchurch', 
        'Waikato', 'Hamilton', 'Bay of Plenty', 'Tauranga',
        'Otago', 'Dunedin', 'Manawatu', 'Palmerston North'
    ]
    
    for location in locations:
        if location.lower() in description.lower():
            return location
    
    return "New Zealand"

def scheduled_email_check():
    """Run every 30 minutes to check for new job emails."""
    print("Running scheduled email check...")
    with app.app_context():
        process_job_emails()

def scheduled_job_search():
    """Run every 3 hours to automatically search for jobs using Apify."""
    print(f"\n{'='*80}")
    print(f"🤖 SCHEDULED AUTO JOB SEARCH (JobCopilot Mode)")
    print(f"{'='*80}")
    
    with app.app_context():
        try:
            # Check if auto search is enabled
            if not USER_SEARCH_CONFIG.get('enabled', True):
                print("⏸️  Auto search is disabled in config")
                return
            
            # Check usage limits
            usage_stats = get_usage_stats()
            print(f"📊 Today's usage: {usage_stats['searches_today']} searches, {usage_stats['jobs_fetched_today']} jobs")
            
            if not can_make_search():
                print("⚠️  Daily search limit reached, skipping this run")
                return
            
            all_jobs_found = []
            total_new_jobs = 0
            total_jobs_from_apify = 0
            jobs_fetched_this_run = 0
            
            # Determine platforms
            platforms_to_search = USER_SEARCH_CONFIG.get('platforms', ['linkedin', 'seek'])
            if 'linkedin' in platforms_to_search and 'seek' in platforms_to_search:
                platform_mode = 'both'
            elif 'linkedin' in platforms_to_search:
                platform_mode = 'linkedin'
            elif 'seek' in platforms_to_search:
                platform_mode = 'seek'
            else:
                print("❌ No platforms configured")
                return
            
            # Search for each keyword
            for keyword in USER_SEARCH_CONFIG['keywords']:
                print(f"\n🔎 Searching for: {keyword}")
                
                jobs_per_keyword = USER_SEARCH_CONFIG['max_jobs_per_search'] // len(USER_SEARCH_CONFIG['keywords'])
                
                if not can_fetch_jobs(jobs_per_keyword, jobs_fetched_this_run):
                    print(f"⚠️  Daily job limit would be exceeded, stopping search")
                    break
                
                jobs = search_jobs_apify(
                    keywords=keyword,
                    location=USER_SEARCH_CONFIG['location'],
                    max_jobs=jobs_per_keyword,
                    platform=platform_mode,
                    remote_only=USER_SEARCH_CONFIG.get('remote_ok', False)
                )
                
                print(f"   Found {len(jobs)} jobs for '{keyword}'")
                total_jobs_from_apify += len(jobs)
                jobs_fetched_this_run += len(jobs)
                all_jobs_found.extend(jobs)
            
            # Process each job
            record_search(jobs_fetched_this_run)
            
            for job in all_jobs_found:
                # Analyze with AI
                print(f"\n🤖 Analyzing: {job['job_title']} at {job['company_name']}")
                ai_result = analyze_job_match(job)
                job['match_score'] = ai_result['match_score']
                job['ai_analysis'] = ai_result['analysis']
                
                # Save to database
                job_id = insert_job(job)
                if job_id:
                    total_new_jobs += 1
                    job['id'] = job_id
                    print(f"  ✅ Match Score: {job['match_score']}%")
                    
                    # Auto-apply if 70%+ match
                    if should_auto_apply(job):
                        print(f"  🎯 Auto-applying (70%+ match)...")
                        auto_apply_to_job(job)
            
            print(f"\n{'='*80}")
            print(f"✅ SCHEDULED AUTO SEARCH COMPLETE!")
            print(f"   New jobs found: {total_new_jobs}")
            print(f"   Jobs fetched from Apify: {total_jobs_from_apify}")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"❌ Error in scheduled job search: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_db()
    
    scheduler = BackgroundScheduler()
    
    # Email checking every 30 minutes
    scheduler.add_job(
        func=scheduled_email_check,
        trigger="interval",
        minutes=30,
        id='email_check_job',
        name='Check for new job emails every 30 minutes',
        replace_existing=True
    )
    
    # Automatic job search every 3 hours
    scheduler.add_job(
        func=scheduled_job_search,
        trigger="interval",
        hours=3,
        id='auto_search_job',
        name='Auto-search for jobs every 3 hours (JobCopilot)',
        replace_existing=True
    )
    
    scheduler.start()
    
    print("🚀 Job Application System Starting...")
    print("📧 Email checking scheduled every 30 minutes")
    print("🔍 Auto job search scheduled every 3 hours (JobCopilot Mode)")
    print("🔐 Authentication enabled")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
