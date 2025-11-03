import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, get_all_jobs, get_job_stats, update_job_status, insert_job
from gmail_service import process_job_emails, complete_auth_with_code
from job_fetcher import fetch_job_from_url
from job_fetcher_apify import search_jobs_apify, fetch_job_from_url_apify
from ai_matcher import analyze_job_match
from job_search_config import USER_SEARCH_CONFIG, EXCLUDED_KEYWORDS
from apify_cost_tracker import can_make_search, can_fetch_jobs, record_search, get_usage_stats
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
    
    min_score = request.args.get('min_score')
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
            
            # Try Apify first, fall back to basic scraping
            job_data = fetch_job_from_url_apify(url)
            if not job_data:
                job_data = fetch_job_from_url(url)
            
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
        
        # Search for each keyword
        for keyword in USER_SEARCH_CONFIG['keywords']:
            print(f"\n🔎 Searching for: {keyword}")
            
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
                    total_new_jobs += 1
                    all_jobs_found.append(job_data)
                    print(f"   💾 Saved (ID: {job_id})")
        
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

def scheduled_email_check():
    """Run every 30 minutes to check for new job emails."""
    print("Running scheduled email check...")
    with app.app_context():
        process_job_emails()

if __name__ == '__main__':
    init_db()
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=scheduled_email_check,
        trigger="interval",
        minutes=30,
        id='email_check_job',
        name='Check for new job emails every 30 minutes',
        replace_existing=True
    )
    scheduler.start()
    
    print("🚀 Job Application System Starting...")
    print("📧 Email checking scheduled every 30 minutes")
    print("🔐 Authentication enabled")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
