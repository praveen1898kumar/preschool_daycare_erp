import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'little-millennium-kharadi-super-secret-key-2026')
    CAMPUS_NAME = "Little Millennium - Nest Daycare (Kharadi Branch)"
    CAMPUS_CODE = "LM-NEST-KHD"
    CAMPUS_ADDRESS = "Survey No. 42/1, Kharadi Bypass Rd, Near EON IT Park, Kharadi, Pune, Maharashtra 411014"
    CAMPUS_PHONE = "+91 98230 45678"
    CAMPUS_EMAIL = "kharadi@littlemillennium.com"
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preschool_erp.db')
    
    # State & National Daycare Regulatory Student-to-Teacher Ratio standards
    RATIO_RULES = {
        'Infant Care': {'max_ratio': 3, 'desc': '1 Teacher per 3 Infants (Max class: 9)'},
        'Toddler Nest': {'max_ratio': 5, 'desc': '1 Teacher per 5 Toddlers (Max class: 15)'},
        'Playgroup': {'max_ratio': 7, 'desc': '1 Teacher per 7 Children (Max class: 14)'},
        'Pre-K / Kindergarten': {'max_ratio': 8, 'desc': '1 Teacher per 8 Children (Max class: 16)'},
        'After-School Daycare': {'max_ratio': 10, 'desc': '1 Teacher per 10 Children (Max class: 20)'}
    }
