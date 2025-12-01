#!/usr/bin/env python3
"""
Smart Import Script - Imports new jobs AND updates existing job descriptions.
Avoids duplicates by matching on URL, and falls back to title+employer matching.
"""

import csv
import sqlite3
from ai_matcher import analyze_job_match
from auto_apply import auto_apply_to_job, should_auto_apply
from database import job_exists, insert_job

def smart_import_csv(csv_path):
    """
    Smart import that:
    1. Updates descriptions for existing jobs (matched by URL or title+employer)
    2. Imports NEW jobs that don't exist yet
    3. Avoids duplicates
    """
    print(f"\n{'='*80}")
    print(f"🚀 SMART IMPORT - Import New + Update Existing")
    print(f"{'='*80}")
    
    conn = sqlite3.connect('jobs.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','
        f.seek(0)
        
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)
    
    print(f"   📋 Found {len(rows)} jobs in CSV")
    print(f"   📋 Columns: {list(rows[0].keys()) if rows else 'None'}")
    
    stats = {
        'descriptions_updated': 0,
        'new_jobs_imported': 0,
        'duplicates_skipped': 0,
        'errors': 0,
        'auto_applied': 0
    }
    
    for i, row in enumerate(rows):
        try:
            title = row.get('Title', row.get('Position', '')).strip()
            employer = row.get('Employer', row.get('Hiring Company', '')).strip()
            link = row.get('Link', row.get('Application Link', '')).strip()
            description = row.get('Description', '').strip()
            email = row.get('Email', row.get('Contact Email', '')).strip()
            employment_type = row.get('Employment Type', '').strip()
            
            if not title or not link:
                continue
            
            if email == 'N/A' or not email or '@' not in email:
                email = None
            
            cursor.execute('SELECT id, description, status FROM jobs WHERE job_url = ?', (link,))
            existing_job = cursor.fetchone()
            
            if existing_job:
                current_desc = existing_job['description'] or ''
                if len(description) > 50 and len(current_desc) < 50:
                    cursor.execute('''
                        UPDATE jobs SET description = ? WHERE id = ?
                    ''', (description[:5000], existing_job['id']))
                    conn.commit()
                    stats['descriptions_updated'] += 1
                    print(f"   📝 Updated description: {title[:40]}...")
                else:
                    stats['duplicates_skipped'] += 1
                continue
            
            if not existing_job and title and employer:
                cursor.execute('''
                    SELECT id, description, status FROM jobs 
                    WHERE LOWER(job_title) LIKE LOWER(?) 
                    AND LOWER(company_name) LIKE LOWER(?)
                ''', (f'%{title[:30]}%', f'%{employer[:20]}%'))
                title_match = cursor.fetchone()
                
                if title_match:
                    current_desc = title_match['description'] or ''
                    if len(description) > 50 and len(current_desc) < 50:
                        cursor.execute('''
                            UPDATE jobs SET description = ? WHERE id = ?
                        ''', (description[:5000], title_match['id']))
                        conn.commit()
                        stats['descriptions_updated'] += 1
                        print(f"   📝 Updated (title match): {title[:40]}...")
                    else:
                        stats['duplicates_skipped'] += 1
                    continue
            
            print(f"\n   🆕 NEW JOB [{i+1}/{len(rows)}]: {title[:50]}")
            print(f"      School: {employer}")
            print(f"      Email: {email or 'None'}")
            
            job_for_analysis = {
                'job_title': title,
                'company_name': employer,
                'description': description,
                'job_url': link
            }
            ai_result = analyze_job_match(job_for_analysis)
            match_score = ai_result.get('match_score', 0)
            ai_analysis = ai_result.get('analysis', '')
            
            fetched_desc = ai_result.get('fetched_description', '')
            if fetched_desc and len(fetched_desc) > len(description):
                description = fetched_desc
            
            print(f"      Match Score: {match_score}%")
            
            job_data = {
                'job_title': title,
                'company_name': employer,
                'location': 'New Zealand',
                'job_url': link,
                'description': description[:5000] if description else '',
                'posted_date': '',
                'source_platform': 'Education Gazette NZ (CSV Import)',
                'salary_info': employment_type,
                'status': 'new',
                'match_score': match_score,
                'ai_analysis': ai_analysis,
                'contact_email': email
            }
            
            job_id = insert_job(job_data)
            
            if job_id:
                stats['new_jobs_imported'] += 1
                
                if email:
                    cursor.execute('''
                        UPDATE jobs SET email_id = ? WHERE id = ?
                    ''', (email, job_id))
                    conn.commit()
                
                if match_score >= 70 and email:
                    print(f"      🎯 High match with email - attempting auto-apply...")
                    job_data['id'] = job_id
                    apply_result = auto_apply_to_job(job_data)
                    if apply_result.get('success'):
                        stats['auto_applied'] += 1
                        print(f"      ✅ Application sent!")
            else:
                stats['duplicates_skipped'] += 1
                
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            stats['errors'] += 1
            continue
    
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ SMART IMPORT COMPLETE!")
    print(f"   New jobs imported: {stats['new_jobs_imported']}")
    print(f"   Descriptions updated: {stats['descriptions_updated']}")
    print(f"   Duplicates skipped: {stats['duplicates_skipped']}")
    print(f"   Auto-applications sent: {stats['auto_applied']}")
    print(f"   Errors: {stats['errors']}")
    print(f"{'='*80}\n")
    
    return stats

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = 'gazette_jobs_fresh.csv'
    
    smart_import_csv(csv_path)
