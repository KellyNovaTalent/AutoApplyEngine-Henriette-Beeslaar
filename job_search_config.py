"""
JobCopilot-style automated job search configuration.
User can set their job search preferences here.
"""

USER_SEARCH_CONFIG = {
    'enabled': True,  # Enable/disable automatic scheduled job searching
    'keywords': [
        # Foundation Phase (Grades R-3, Ages 5-9)
        'Foundation Phase Teacher',
        'Grade R Teacher',
        'Grade 1 Teacher',
        'Grade 2 Teacher', 
        'Grade 3 Teacher',
        'Junior Primary Teacher',
        'ECD Teacher',
        'Early Childhood Teacher',
        
        # Primary School (General)
        'Primary School Teacher',
        'Primary Teacher',
        'Elementary Teacher',
        
        # NZ-specific terms
        'Years 1-4 Teacher',
        'New Entrant Teacher',
        'Junior School Teacher'
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
