"""
Tests for the Instagram Scraper functionality
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from scraper import InstagramScraper
from models import InstagramPost


class TestInstagramScraperInit:
    """Tests for InstagramScraper initialization"""
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly"""
        scraper = InstagramScraper()
        assert scraper.openai_client is not None
    
    @patch('scraper.Config.OPENAI_API_KEY', None)
    def test_scraper_initialization_no_api_key(self):
        """Test scraper initialization without API key"""
        with pytest.raises(Exception):
            InstagramScraper()


class TestScrapeInstagramPost:
    """Tests for the main scraping functionality"""
    
    @pytest.mark.asyncio
    async def test_scrape_instagram_post_success(self, sample_instagram_post, sample_scraped_content):
        """Test successful Instagram post scraping"""
        scraper = InstagramScraper()
        
        with patch.object(scraper, '_scrape_with_crawl4ai_retry') as mock_crawl, \
             patch.object(scraper, '_parse_with_openai') as mock_parse:
            
            mock_crawl.return_value = sample_scraped_content
            mock_parse.return_value = sample_instagram_post
            
            result = await scraper.scrape_instagram_post("https://www.instagram.com/p/TEST123/")
            
            assert result is not None
            assert isinstance(result, InstagramPost)
            assert result.url == "https://www.instagram.com/p/TEST123/"
            mock_crawl.assert_called_once()
            mock_parse.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_instagram_post_no_content(self):
        """Test scraping when no content is retrieved"""
        scraper = InstagramScraper()
        
        with patch.object(scraper, '_scrape_with_crawl4ai_retry') as mock_crawl:
            mock_crawl.return_value = None
            
            with pytest.raises(Exception, match="Failed to retrieve content"):
                await scraper.scrape_instagram_post("https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_scrape_instagram_post_parse_failure(self, sample_scraped_content):
        """Test scraping when parsing fails"""
        scraper = InstagramScraper()
        
        with patch.object(scraper, '_scrape_with_crawl4ai_retry') as mock_crawl, \
             patch.object(scraper, '_parse_with_openai') as mock_parse:
            
            mock_crawl.return_value = sample_scraped_content
            mock_parse.return_value = None
            
            with pytest.raises(Exception, match="Failed to parse Instagram content"):
                await scraper.scrape_instagram_post("https://www.instagram.com/p/TEST123/")


class TestCrawl4AIIntegration:
    """Tests for Crawl4AI integration"""
    
    @pytest.mark.asyncio
    async def test_scrape_with_crawl4ai_success(self, mock_crawl4ai_success):
        """Test successful Crawl4AI scraping"""
        scraper = InstagramScraper()
        
        with patch('scraper.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_success
            
            result = await scraper._scrape_with_crawl4ai("https://www.instagram.com/p/TEST123/")
            
            assert result is not None
            assert "testuser" in result
    
    @pytest.mark.asyncio
    async def test_scrape_with_crawl4ai_failure(self, mock_crawl4ai_failure):
        """Test Crawl4AI scraping failure"""
        scraper = InstagramScraper()
        
        with patch('scraper.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_failure
            
            with pytest.raises(Exception, match="Page not found"):
                await scraper._scrape_with_crawl4ai("https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_scrape_with_crawl4ai_private_post(self):
        """Test Crawl4AI scraping private post"""
        scraper = InstagramScraper()
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "403 - Forbidden"
        
        with patch('scraper.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_result
            
            with pytest.raises(Exception, match="Instagram post is private"):
                await scraper._scrape_with_crawl4ai("https://www.instagram.com/p/PRIVATE/")
    
    @pytest.mark.asyncio
    async def test_scrape_with_crawl4ai_rate_limit(self):
        """Test Crawl4AI rate limiting"""
        scraper = InstagramScraper()
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "429 - Too Many Requests"
        
        with patch('scraper.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_result
            
            with pytest.raises(Exception, match="Instagram is rate limiting"):
                await scraper._scrape_with_crawl4ai("https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_scrape_with_crawl4ai_short_content(self):
        """Test Crawl4AI with too short content"""
        scraper = InstagramScraper()
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.markdown = "Short"  # Too short content
        
        with patch('scraper.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_result
            
            result = await scraper._scrape_with_crawl4ai("https://www.instagram.com/p/TEST123/")
            assert result is None


class TestCrawl4AIRetry:
    """Tests for Crawl4AI retry logic"""
    
    @pytest.mark.asyncio
    async def test_scrape_with_retry_success_first_attempt(self, sample_scraped_content):
        """Test successful scraping on first attempt"""
        scraper = InstagramScraper()
        
        with patch.object(scraper, '_scrape_with_crawl4ai') as mock_crawl:
            mock_crawl.return_value = sample_scraped_content
            
            result = await scraper._scrape_with_crawl4ai_retry("https://www.instagram.com/p/TEST123/")
            
            assert result == sample_scraped_content
            mock_crawl.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_with_retry_success_second_attempt(self, sample_scraped_content):
        """Test successful scraping on second attempt"""
        scraper = InstagramScraper()
        
        with patch.object(scraper, '_scrape_with_crawl4ai') as mock_crawl:
            mock_crawl.side_effect = [None, sample_scraped_content]  # Fail first, succeed second
            
            result = await scraper._scrape_with_crawl4ai_retry("https://www.instagram.com/p/TEST123/")
            
            assert result == sample_scraped_content
            assert mock_crawl.call_count == 2
    
    @pytest.mark.asyncio
    async def test_scrape_with_retry_all_attempts_fail(self):
        """Test when all retry attempts fail"""
        scraper = InstagramScraper()
        
        with patch.object(scraper, '_scrape_with_crawl4ai') as mock_crawl:
            mock_crawl.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                await scraper._scrape_with_crawl4ai_retry("https://www.instagram.com/p/TEST123/")
            
            assert mock_crawl.call_count == 3  # Should retry 3 times


class TestOpenAIIntegration:
    """Tests for OpenAI integration"""
    
    @pytest.mark.asyncio
    async def test_parse_with_openai_success(self, sample_scraped_content, mock_openai_response):
        """Test successful OpenAI parsing"""
        scraper = InstagramScraper()
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_function_call = Mock()
            
            mock_function_call.arguments = json.dumps(mock_openai_response)
            mock_message.function_call = mock_function_call
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            mock_create.return_value = mock_response
            
            result = await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/TEST123/")
            
            assert result is not None
            assert isinstance(result, InstagramPost)
            assert result.caption == "Test post with #hashtag and @mention"
            assert result.url == "https://www.instagram.com/p/TEST123/"
    
    @pytest.mark.asyncio
    async def test_parse_with_openai_no_function_call(self, sample_scraped_content):
        """Test OpenAI parsing when no function call is returned"""
        scraper = InstagramScraper()
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.function_call = None
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            mock_create.return_value = mock_response
            
            with pytest.raises(Exception, match="OpenAI failed to parse"):
                await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_parse_with_openai_invalid_json(self, sample_scraped_content):
        """Test OpenAI parsing with invalid JSON response"""
        scraper = InstagramScraper()
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_function_call = Mock()
            
            mock_function_call.arguments = "invalid json"
            mock_message.function_call = mock_function_call
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            mock_create.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to parse OpenAI response"):
                await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_parse_with_openai_api_key_error(self, sample_scraped_content):
        """Test OpenAI parsing with API key error"""
        scraper = InstagramScraper()
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("Invalid API key")
            
            with pytest.raises(Exception, match="OpenAI API key is invalid"):
                await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_parse_with_openai_quota_error(self, sample_scraped_content):
        """Test OpenAI parsing with quota exceeded error"""
        scraper = InstagramScraper()
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("Quota exceeded for billing")
            
            with pytest.raises(Exception, match="OpenAI API quota exceeded"):
                await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/TEST123/")
    
    @pytest.mark.asyncio
    async def test_parse_with_openai_rate_limit_error(self, sample_scraped_content):
        """Test OpenAI parsing with rate limit error"""
        scraper = InstagramScraper()
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("Rate limit exceeded")
            
            with pytest.raises(Exception, match="OpenAI API rate limit exceeded"):
                await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/TEST123/")


class TestPostTypeExtraction:
    """Tests for different Instagram post types"""
    
    @pytest.mark.parametrize("post_type,content_indicator", [
        ("image", "Image post"),
        ("video", "Video content"),
        ("carousel", "Multiple images"),
    ])
    @pytest.mark.asyncio
    async def test_parse_different_post_types(self, post_type, content_indicator, mock_openai_response):
        """Test parsing different Instagram post types"""
        scraper = InstagramScraper()
        
        # Modify response for specific post type
        mock_openai_response["type"] = post_type
        content = f"# Instagram Post\n\n{content_indicator}\n\n**testuser** Test content"
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_function_call = Mock()
            
            mock_function_call.arguments = json.dumps(mock_openai_response)
            mock_message.function_call = mock_function_call
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            mock_create.return_value = mock_response
            
            result = await scraper._parse_with_openai(content, "https://www.instagram.com/p/TEST123/")
            
            assert result.type == post_type


class TestShortCodeExtraction:
    """Tests for short code extraction functionality"""
    
    @pytest.mark.asyncio
    async def test_shortcode_extraction_from_url(self, sample_scraped_content):
        """Test short code extraction from URL when not provided by OpenAI"""
        scraper = InstagramScraper()
        
        mock_response = {
            "caption": "Test post",
            "type": "image",
            "url": "https://www.instagram.com/p/ABC123/",
            "ownerUsername": "testuser"
            # Note: shortCode is missing, should be extracted from URL
        }
        
        with patch.object(scraper.openai_client.chat.completions, 'create') as mock_create:
            mock_response_obj = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_function_call = Mock()
            
            mock_function_call.arguments = json.dumps(mock_response)
            mock_message.function_call = mock_function_call
            mock_choice.message = mock_message
            mock_response_obj.choices = [mock_choice]
            
            mock_create.return_value = mock_response_obj
            
            result = await scraper._parse_with_openai(sample_scraped_content, "https://www.instagram.com/p/ABC123/")
            
            assert result.shortCode == "ABC123"


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 