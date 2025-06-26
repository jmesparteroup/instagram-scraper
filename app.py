#!/usr/bin/env python3
"""
Instagram Scraper API
Flask application with rate limiting, logging, and comprehensive error handling
"""

import asyncio
import logging
import traceback
from typing import Dict, Any
from datetime import datetime

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pydantic import ValidationError

from config import Config
from models import ScrapeRequest, ScrapeResponse, InstagramPost
from scraper import InstagramScraper

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Setup logging
Config.setup_logging()
logger = logging.getLogger(__name__)

# Validate configuration
try:
    Config.validate_config()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    exit(1)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.DEFAULT_RATE_LIMIT],
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# Initialize scraper
scraper = InstagramScraper()

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded from {get_remote_address()}: {e}")
    return jsonify({
        "success": False,
        "error": "Rate limit exceeded. Please try again later.",
        "retry_after": getattr(e, 'retry_after', None)
    }), 429

@app.errorhandler(ValidationError)
def validation_error_handler(e):
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error: {e}")
    return jsonify({
        "success": False,
        "error": "Invalid request data",
        "details": str(e)
    }), 400

@app.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

@app.errorhandler(Exception)
def general_error_handler(e):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
    return jsonify({
        "success": False,
        "error": "An unexpected error occurred"
    }), 500

# Routes
@app.route('/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.route('/scrape', methods=['POST'])
@limiter.limit(Config.SCRAPE_RATE_LIMIT)
def scrape_instagram():
    """
    Scrape Instagram post endpoint
    
    Expected payload:
    {
        "instagram_url": "https://www.instagram.com/p/XXXXXXXXX/"
    }
    """
    try:
        logger.info(f"Scrape request received from {get_remote_address()}")
        
        # Validate request data
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Content-Type must be application/json"
            }), 400
        
        # Parse and validate request
        try:
            request_data = ScrapeRequest(**request.get_json())
        except ValidationError as e:
            logger.error(f"Request validation failed: {e}")
            return jsonify({
                "success": False,
                "error": "Invalid request format",
                "details": [err["msg"] for err in e.errors()]
            }), 400
        
        # Validate Instagram URL format
        if not _is_valid_instagram_url(request_data.instagram_url):
            return jsonify({
                "success": False,
                "error": "Invalid Instagram URL format"
            }), 400
        
        logger.info(f"Starting scrape for URL: {request_data.instagram_url}")
        
        # Perform scraping
        try:
            # Run async scraping in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            post_data = loop.run_until_complete(
                asyncio.wait_for(
                    scraper.scrape_instagram_post(request_data.instagram_url),
                    timeout=Config.SCRAPE_TIMEOUT
                )
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Scraping timeout for URL: {request_data.instagram_url}")
            return jsonify({
                "success": False,
                "error": "Scraping timeout. The request took too long to process."
            }), 408
            
        except Exception as e:
            logger.error(f"Scraping error for URL {request_data.instagram_url}: {e}")
            return _handle_scraping_error(e)
        
        finally:
            loop.close()
        
        # Handle scraping result
        if post_data is None:
            logger.warning(f"No data extracted from URL: {request_data.instagram_url}")
            return jsonify({
                "success": False,
                "error": "Unable to extract data from Instagram post. The post may be private or inaccessible."
            }), 404
        
        logger.info(f"Successfully scraped URL: {request_data.instagram_url}")
        
        # Return successful response
        response = ScrapeResponse(success=True, data=post_data)
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Unexpected error in scrape endpoint: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred during scraping"
        }), 500

def _is_valid_instagram_url(url: str) -> bool:
    """Validate Instagram URL format"""
    import re
    
    patterns = [
        r'^https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?$',  # Post URL
        r'^https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?$',  # Reel URL
        r'^https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?$',  # IGTV URL
    ]
    
    return any(re.match(pattern, url) for pattern in patterns)

def _handle_scraping_error(error: Exception) -> tuple:
    """Handle different types of scraping errors"""
    error_message = str(error).lower()
    
    # Instagram access errors
    if any(keyword in error_message for keyword in ['private', 'not found', '404', 'access denied']):
        return jsonify({
            "success": False,
            "error": "Instagram post is private, deleted, or not accessible"
        }), 404
    
    # Instagram rate limiting or blocking
    if any(keyword in error_message for keyword in ['rate limit', 'blocked', 'too many requests']):
        return jsonify({
            "success": False,
            "error": "Instagram is rate limiting requests. Please try again later."
        }), 429
    
    # OpenAI API errors
    if any(keyword in error_message for keyword in ['openai', 'api key', 'quota', 'billing']):
        return jsonify({
            "success": False,
            "error": "AI processing service is temporarily unavailable"
        }), 503
    
    # Network errors
    if any(keyword in error_message for keyword in ['network', 'connection', 'timeout']):
        return jsonify({
            "success": False,
            "error": "Network error occurred. Please try again."
        }), 503
    
    # Generic error
    return jsonify({
        "success": False,
        "error": "An error occurred during scraping"
    }), 500

if __name__ == '__main__':
    logger.info("Starting Instagram Scraper API")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    ) 