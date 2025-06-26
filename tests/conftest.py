"""
Pytest configuration and shared fixtures for Instagram Scraper API tests
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch
from flask import Flask
import json

# Set test environment variables before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['OPENAI_API_KEY'] = 'test-api-key'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'  # Use different DB for tests

from app import app
from scraper import InstagramScraper
from models import InstagramPost


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    app.config['RATELIMIT_ENABLED'] = False  # Disable rate limiting for tests
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def scraper():
    """Create an InstagramScraper instance for testing"""
    return InstagramScraper()


@pytest.fixture
def sample_instagram_post():
    """Sample Instagram post data for testing"""
    return InstagramPost(
        caption="Test post with #hashtag and @mention",
        type="image",
        url="https://www.instagram.com/p/TEST123/",
        shortCode="TEST123",
        timestamp="2024-01-01T12:00:00Z",
        likesCount=100,
        commentsCount=10,
        ownerUsername="testuser",
        ownerFullName="Test User",
        hashtags=["hashtag"],
        mentions=["mention"]
    )


@pytest.fixture
def sample_scraped_content():
    """Sample scraped content from Instagram"""
    return """
    # Instagram Post
    
    **testuser** (Test User)
    
    Test post with #hashtag and @mention
    
    Posted 2 hours ago
    
    100 likes • 10 comments
    
    View on Instagram
    """


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "caption": "Test post with #hashtag and @mention",
        "type": "image",
        "url": "https://www.instagram.com/p/TEST123/",
        "shortCode": "TEST123",
        "timestamp": "2024-01-01T12:00:00Z",
        "likesCount": 100,
        "commentsCount": 10,
        "ownerUsername": "testuser",
        "ownerFullName": "Test User",
        "hashtags": ["hashtag"],
        "mentions": ["mention"]
    }


@pytest.fixture
def instagram_urls():
    """Sample Instagram URLs for different post types"""
    return {
        "image_post": "https://www.instagram.com/p/IMG123/",
        "video_post": "https://www.instagram.com/p/VID456/", 
        "reel": "https://www.instagram.com/reel/REEL789/",
        "carousel": "https://www.instagram.com/p/CAR012/",
        "invalid": "https://example.com/not-instagram"
    }


@pytest.fixture
def mock_crawl4ai_success():
    """Mock successful Crawl4AI response"""
    mock_result = Mock()
    mock_result.success = True
    mock_result.markdown = """
    # Instagram Post
    
    **testuser** (Test User)
    
    Test post content with #hashtag and @mention
    
    Posted 2 hours ago
    
    100 likes • 10 comments
    """
    return mock_result


@pytest.fixture
def mock_crawl4ai_failure():
    """Mock failed Crawl4AI response"""
    mock_result = Mock()
    mock_result.success = False
    mock_result.error_message = "404 - Page not found"
    return mock_result


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Utility functions for tests
def create_mock_openai_client(response_data):
    """Create a mock OpenAI client with specified response data"""
    mock_client = Mock()
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()
    mock_function_call = Mock()
    
    mock_function_call.arguments = json.dumps(response_data)
    mock_message.function_call = mock_function_call
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# Test data constants
TEST_INSTAGRAM_URLS = {
    "valid_image": "https://www.instagram.com/p/TEST123/",
    "valid_video": "https://www.instagram.com/p/VIDEO456/",
    "valid_reel": "https://www.instagram.com/reel/REEL789/",
    "valid_carousel": "https://www.instagram.com/p/CAROUSEL/",
    "invalid_format": "https://example.com/invalid",
    "private_post": "https://www.instagram.com/p/PRIVATE/",
    "deleted_post": "https://www.instagram.com/p/DELETED/"
} 