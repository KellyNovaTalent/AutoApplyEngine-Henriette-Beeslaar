"""
JobCopilot-style automated job search configuration.
User can set their job search preferences here.
"""

USER_SEARCH_CONFIG = {
    'enabled': True,  # Enable/disable automatic scheduled job searching
    'keywords': [
        'Foundation Phase Teacher',
        'Primary School Teacher',
        'Special Education Teacher',
        'Learning Support',
        'SENCO'
    ],
    'location': 'New Zealand',
    'max_jobs_per_search': 10,  # Start small for testing
    'platforms': ['linkedin', 'seek'],  
    'remote_ok': False,
    'salary_min': None,
    'auto_apply_enabled': True,  
    'auto_apply_threshold': 70,  
    'review_mode': False  
}

EXCLUDED_KEYWORDS = [
    'secondary',
    'high school',
    'college',
    'university',
    'lecturer'
]
