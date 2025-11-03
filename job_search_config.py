"""
JobCopilot-style automated job search configuration.
User can set their job search preferences here.
"""

USER_SEARCH_CONFIG = {
    'enabled': True,
    'keywords': [
        'Foundation Phase Teacher',
        'Primary School Teacher',
        'Special Education Teacher',
        'Learning Support',
        'SENCO'
    ],
    'location': 'New Zealand',
    'max_jobs_per_search': 50,
    'platforms': ['linkedin', 'seek'],  
    'remote_ok': True,
    'salary_min': None,
    'auto_apply_enabled': False,  
    'auto_apply_threshold': 80,  
    'review_mode': True  
}

EXCLUDED_KEYWORDS = [
    'secondary',
    'high school',
    'college',
    'university',
    'lecturer'
]
