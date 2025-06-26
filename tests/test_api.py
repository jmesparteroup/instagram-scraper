"""
Tests for the Instagram Scraper API endpoints
"""

import json
import pytest
from unittest.mock import patch, Mock
from models import InstagramPost


class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test health check returns 200 and correct format"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['version'] == '1.0.0'
    
    def test_health_check_method_not_allowed(self, client):
        """Test health check only accepts GET requests"""
        response = client.post('/health')
        assert response.status_code == 405


class TestScrapeEndpoint:
    """Tests for the Instagram scraping endpoint"""
    
    def test_scrape_endpoint_success(self, client, sample_instagram_post):
        """Test successful scraping request"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = sample_instagram_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert data['data'] is not None
            assert data['data']['url'] == 'https://www.instagram.com/p/TEST123/'
    
    def test_scrape_endpoint_invalid_json(self, client):
        """Test request with invalid JSON"""
        response = client.post('/scrape', 
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'json' in data['error'].lower()
    
    def test_scrape_endpoint_missing_content_type(self, client):
        """Test request without proper Content-Type header"""
        response = client.post('/scrape', 
            data=json.dumps({'instagram_url': 'https://www.instagram.com/p/TEST123/'})
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Content-Type' in data['error']
    
    def test_scrape_endpoint_missing_url(self, client):
        """Test request without instagram_url field"""
        response = client.post('/scrape', 
            json={},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'instagram_url' in str(data['details']).lower()
    
    def test_scrape_endpoint_invalid_url_format(self, client):
        """Test request with invalid Instagram URL format"""
        response = client.post('/scrape', 
            json={'instagram_url': 'https://example.com/not-instagram'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid Instagram URL format' in data['error']
    
    @pytest.mark.parametrize("valid_url", [
        "https://www.instagram.com/p/TEST123/",
        "https://instagram.com/p/TEST123/",
        "https://www.instagram.com/reel/TEST123/",
        "https://instagram.com/reel/TEST123/",
        "http://www.instagram.com/p/TEST123/",
        "https://www.instagram.com/p/TEST123",  # Without trailing slash
    ])
    def test_scrape_endpoint_valid_url_formats(self, client, valid_url, sample_instagram_post):
        """Test various valid Instagram URL formats"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = sample_instagram_post
            
            response = client.post('/scrape', 
                json={'instagram_url': valid_url},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
    
    def test_scrape_endpoint_scraping_timeout(self, client):
        """Test scraping timeout handling"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            import asyncio
            mock_scrape.side_effect = asyncio.TimeoutError()
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 408
            data = response.get_json()
            assert data['success'] is False
            assert 'timeout' in data['error'].lower()
    
    def test_scrape_endpoint_no_data_extracted(self, client):
        """Test when no data is extracted from Instagram post"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = None
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert 'private or inaccessible' in data['error']
    
    def test_scrape_endpoint_instagram_access_error(self, client):
        """Test Instagram access restriction errors"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.side_effect = Exception("Instagram post is private or access denied")
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert 'private' in data['error']
    
    def test_scrape_endpoint_instagram_rate_limit_error(self, client):
        """Test Instagram rate limiting errors"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.side_effect = Exception("Instagram is rate limiting requests")
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 429
            data = response.get_json()
            assert data['success'] is False
            assert 'rate limiting' in data['error']
    
    def test_scrape_endpoint_openai_error(self, client):
        """Test OpenAI API errors"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.side_effect = Exception("OpenAI API key is invalid")
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert data['success'] is False
            assert 'AI processing service' in data['error']


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_error_handling(self, client):
        """Test 404 error for non-existent endpoints"""
        response = client.get('/non-existent-endpoint')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed for scrape endpoint"""
        response = client.get('/scrape')
        assert response.status_code == 405
    
    def test_internal_server_error_handling(self, client):
        """Test internal server error handling"""
        with patch('app.scraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.side_effect = Exception("Unexpected error")
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            # Should handle the error gracefully
            assert response.status_code in [500, 503, 404, 429]  # Various error codes possible
            data = response.get_json()
            assert data['success'] is False


class TestRateLimiting:
    """Tests for rate limiting functionality"""
    
    @pytest.mark.skipif(
        True,  # Skip by default as it requires Redis
        reason="Rate limiting tests require Redis server"
    )
    def test_rate_limiting_enabled(self, client):
        """Test that rate limiting works when enabled"""
        # Make multiple requests quickly
        for i in range(10):
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 429:
                # Rate limit was hit
                data = response.get_json()
                assert data['success'] is False
                assert 'rate limit' in data['error'].lower()
                break
        else:
            pytest.skip("Rate limiting not triggered - Redis may not be configured")


class TestPostTypeHandling:
    """Tests for different Instagram post types"""
    
    @pytest.mark.parametrize("post_type,expected_url", [
        ("image", "https://www.instagram.com/p/IMG123/"),
        ("video", "https://www.instagram.com/p/VID456/"),
        ("carousel", "https://www.instagram.com/p/CAR789/"),
    ])
    def test_different_post_types(self, client, post_type, expected_url, sample_instagram_post):
        """Test scraping different types of Instagram posts"""
        # Modify sample post for specific type
        sample_instagram_post.type = post_type
        sample_instagram_post.url = expected_url
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = sample_instagram_post
            
            response = client.post('/scrape', 
                json={'instagram_url': expected_url},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['data']['type'] == post_type
            assert data['data']['url'] == expected_url


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 