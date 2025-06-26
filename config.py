import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Rate Limiting Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    RATELIMIT_STORAGE_URL = REDIS_URL
    
    # Default rate limits
    DEFAULT_RATE_LIMIT = os.getenv('DEFAULT_RATE_LIMIT', '10 per minute')
    SCRAPE_RATE_LIMIT = os.getenv('SCRAPE_RATE_LIMIT', '5 per minute')
    
    # Timeout Configuration
    SCRAPE_TIMEOUT = int(os.getenv('SCRAPE_TIMEOUT', '60'))  # seconds
    OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '30'))  # seconds
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Instagram Scraping Configuration
    INSTAGRAM_MAX_RETRIES = int(os.getenv('INSTAGRAM_MAX_RETRIES', '3'))
    INSTAGRAM_RETRY_DELAY = int(os.getenv('INSTAGRAM_RETRY_DELAY', '2'))  # seconds
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=cls.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('instagram_scraper.log')
            ]
        )
        
        # Reduce noise from external libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING) 