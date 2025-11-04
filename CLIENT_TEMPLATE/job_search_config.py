"""
JobCopilot-style automated job search configuration.
User can set their job search preferences here.
"""

USER_SEARCH_CONFIG = {
    'enabled': True,  # Enable/disable automatic scheduled job searching
    'keywords': [
        # Optimized for speed - 3 most common NZ teaching job titles
        'Primary Teacher',
        'Junior Primary Teacher',
        'New Entrant Teacher'
    ],
    'location': 'New Zealand',
    'max_jobs_per_search': 15,  # 5 jobs per keyword = 15 total
    'platforms': ['seek'],  # LinkedIn requires payment, Seek works fine
    'remote_ok': False,
    'salary_min': None,
    'auto_apply_enabled': True,  
    'auto_apply_threshold': 70,  
    'review_mode': False  
}

# Exclude roles outside Foundation Phase / Junior Primary
EXCLUDED_KEYWORDS = [
    'secondary',
    'high school',
    'intermediate',
    'senior phase',
    'grade 4',
    'grade 5', 
    'grade 6',
    'grade 7',
    'grade 8',
    'grade 9',
    'grade 10',
    'grade 11',
    'grade 12',
    'college',
    'university',
    'lecturer',
    'tutor',
    'assistant principal',
    'deputy principal',
    'head of department',
    'HOD'
]
