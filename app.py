import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, get_all_jobs, get_job_stats, update_job_status
from gmail_service import process_job_emails, get_auth_url, complete_auth
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
        complete_auth(auth_code)
        result = process_job_emails()
        return jsonify(result)
    except Exception as e:
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
