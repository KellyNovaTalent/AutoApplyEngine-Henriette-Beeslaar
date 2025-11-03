import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

DATABASE_PATH = 'jobs.db'

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company_name TEXT,
            location TEXT,
            description TEXT,
            job_url TEXT UNIQUE NOT NULL,
            posted_date TEXT,
            source_platform TEXT NOT NULL,
            salary_info TEXT,
            date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new',
            rejection_reason TEXT,
            match_score INTEGER DEFAULT 0,
            ai_analysis TEXT,
            application_date TIMESTAMP,
            notes TEXT,
            email_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'ai_analysis' not in columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN ai_analysis TEXT')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT UNIQUE NOT NULL,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DATABASE_PATH)

def job_exists(job_url: str) -> bool:
    """Check if a job with the given URL already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM jobs WHERE job_url = ?', (job_url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def email_processed(email_id: str) -> bool:
    """Check if an email has already been processed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM email_tracking WHERE email_id = ?', (email_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def mark_email_processed(email_id: str):
    """Mark an email as processed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO email_tracking (email_id) VALUES (?)', (email_id,))
    conn.commit()
    conn.close()

def insert_job(job_data: Dict[str, Any]) -> Optional[int]:
    """Insert a new job into the database."""
    if job_exists(job_data['job_url']):
        print(f"Job already exists: {job_data['job_url']}")
        return None
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO jobs (
            job_title, company_name, location, description, job_url,
            posted_date, source_platform, salary_info, status, 
            rejection_reason, match_score, ai_analysis, email_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_data.get('job_title'),
        job_data.get('company_name'),
        job_data.get('location'),
        job_data.get('description'),
        job_data.get('job_url'),
        job_data.get('posted_date'),
        job_data.get('source_platform'),
        job_data.get('salary_info'),
        job_data.get('status', 'new'),
        job_data.get('rejection_reason'),
        job_data.get('match_score', 0),
        job_data.get('ai_analysis'),
        job_data.get('email_id')
    ))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"Inserted job: {job_data.get('job_title')} at {job_data.get('company_name')}")
    return job_id

def get_all_jobs(filters: Optional[Dict] = None) -> List[Dict]:
    """Get all jobs with optional filters."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM jobs'
    params = []
    
    if filters:
        conditions = []
        if filters.get('source_platform'):
            conditions.append('source_platform = ?')
            params.append(filters['source_platform'])
        if filters.get('status'):
            conditions.append('status = ?')
            params.append(filters['status'])
        if filters.get('min_score'):
            conditions.append('match_score >= ?')
            params.append(filters['min_score'])
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY date_received DESC'
    
    cursor.execute(query, params)
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jobs

def get_job_stats() -> Dict[str, Any]:
    """Get statistics about jobs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM jobs')
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'auto-rejected'")
    auto_rejected = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
    applied = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
    new_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT source_platform, COUNT(*) FROM jobs GROUP BY source_platform")
    by_platform = dict(cursor.fetchall())
    
    # Match score categories
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 70")
    high_matches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 50 AND match_score < 70")
    medium_matches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE match_score < 50 OR match_score IS NULL")
    low_matches = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'auto_rejected': auto_rejected,
        'applied': applied,
        'new_jobs': new_jobs,
        'by_platform': by_platform,
        'high_matches': high_matches,
        'medium_matches': medium_matches,
        'low_matches': low_matches
    }

def update_job_status(job_id: int, status: str, notes: Optional[str] = None):
    """Update job status."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status == 'applied':
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, application_date = ?, notes = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat(), notes, job_id))
    else:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, notes = ?
            WHERE id = ?
        ''', (status, notes, job_id))
    
    conn.commit()
    conn.close()
