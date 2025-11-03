"""
Cost and rate limiting tracker for Apify API usage.
Prevents unbounded API costs from automated job searches.
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

TRACKER_FILE = "apify_usage.json"
MAX_SEARCHES_PER_DAY = 10
MAX_JOBS_PER_DAY = 500

def load_usage_tracker():
    """Load the usage tracker from file."""
    if not os.path.exists(TRACKER_FILE):
        return {
            'last_reset': datetime.now().isoformat(),
            'searches_today': 0,
            'jobs_fetched_today': 0
        }
    
    try:
        with open(TRACKER_FILE, 'r') as f:
            data = json.load(f)
            
            # Reset if it's a new day
            last_reset = datetime.fromisoformat(data['last_reset'])
            if datetime.now().date() > last_reset.date():
                return {
                    'last_reset': datetime.now().isoformat(),
                    'searches_today': 0,
                    'jobs_fetched_today': 0
                }
            
            return data
    except Exception as e:
        print(f"Error loading usage tracker: {e}")
        return {
            'last_reset': datetime.now().isoformat(),
            'searches_today': 0,
            'jobs_fetched_today': 0
        }

def save_usage_tracker(data):
    """Save the usage tracker to file."""
    try:
        with open(TRACKER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving usage tracker: {e}")

def can_make_search():
    """Check if we can make another Apify search today."""
    tracker = load_usage_tracker()
    return tracker['searches_today'] < MAX_SEARCHES_PER_DAY

def can_fetch_jobs(num_jobs, current_run_total=0):
    """Check if we can fetch more jobs today, including current run total."""
    tracker = load_usage_tracker()
    total_would_fetch = tracker['jobs_fetched_today'] + current_run_total + num_jobs
    return total_would_fetch <= MAX_JOBS_PER_DAY

def record_search(jobs_fetched):
    """Record an Apify search and jobs fetched."""
    tracker = load_usage_tracker()
    tracker['searches_today'] += 1
    tracker['jobs_fetched_today'] += jobs_fetched
    save_usage_tracker(tracker)

def get_usage_stats():
    """Get current usage statistics."""
    tracker = load_usage_tracker()
    return {
        'searches_today': tracker['searches_today'],
        'searches_remaining': MAX_SEARCHES_PER_DAY - tracker['searches_today'],
        'jobs_fetched_today': tracker['jobs_fetched_today'],
        'jobs_remaining': MAX_JOBS_PER_DAY - tracker['jobs_fetched_today']
    }
