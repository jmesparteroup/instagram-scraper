"""
Tests for Pydantic models
"""

import pytest
from pydantic import ValidationError
from models import InstagramPost, ScrapeRequest, ScrapeResponse


class TestInstagramPost:
    """Tests for InstagramPost model"""
    
    def test_instagram_post_creation_minimal(self):
        """Test creating InstagramPost with minimal data"""
        post = InstagramPost()
        assert post.caption is None
        assert post.type is None
        assert post.url is None
    
    def test_instagram_post_creation_full(self):
        """Test creating InstagramPost with all fields"""
        post = InstagramPost(
            caption="Test caption with #hashtag and @mention",
            type="image",
            url="https://www.instagram.com/p/TEST123/",
            videoUrl="https://example.com/video.mp4",
            imageUrl="https://example.com/image.jpg",
            displayUrl="https://example.com/display.jpg",
            shortCode="TEST123",
            timestamp="2024-01-01T12:00:00Z",
            likesCount=100,
            commentsCount=10,
            videoViewCount=500,
            videoPlayCount=450,
            ownerUsername="testuser",
            ownerFullName="Test User",
            locationName="Test Location",
            hashtags=["hashtag", "test"],
            mentions=["mention", "testuser"],
            alt="Test alt text"
        )
        
        assert post.caption == "Test caption with #hashtag and @mention"
        assert post.type == "image"
        assert post.url == "https://www.instagram.com/p/TEST123/"
        assert post.shortCode == "TEST123"
        assert post.likesCount == 100
        assert post.hashtags == ["hashtag", "test"]
        assert post.mentions == ["mention", "testuser"]
    
    def test_instagram_post_validation_counts(self):
        """Test that count fields accept integers"""
        post = InstagramPost(
            likesCount=100,
            commentsCount=10,
            videoViewCount=500,
            videoPlayCount=450
        )
        
        assert isinstance(post.likesCount, int)
        assert isinstance(post.commentsCount, int)
        assert isinstance(post.videoViewCount, int)
        assert isinstance(post.videoPlayCount, int)
    
    def test_instagram_post_validation_lists(self):
        """Test that list fields accept arrays"""
        post = InstagramPost(
            hashtags=["tag1", "tag2"],
            mentions=["user1", "user2"]
        )
        
        assert isinstance(post.hashtags, list)
        assert isinstance(post.mentions, list)
        assert len(post.hashtags) == 2
        assert len(post.mentions) == 2
    
    def test_instagram_post_empty_lists(self):
        """Test InstagramPost with empty lists"""
        post = InstagramPost(
            hashtags=[],
            mentions=[]
        )
        
        assert post.hashtags == []
        assert post.mentions == []
    
    def test_instagram_post_dict_conversion(self):
        """Test converting InstagramPost to dictionary"""
        post = InstagramPost(
            caption="Test",
            type="image",
            ownerUsername="testuser"
        )
        
        post_dict = post.dict()
        
        assert isinstance(post_dict, dict)
        assert post_dict['caption'] == "Test"
        assert post_dict['type'] == "image"
        assert post_dict['ownerUsername'] == "testuser"
    
    def test_instagram_post_json_serialization(self):
        """Test JSON serialization of InstagramPost"""
        post = InstagramPost(
            caption="Test",
            type="image",
            hashtags=["test"],
            likesCount=100
        )
        
        json_str = post.json()
        assert isinstance(json_str, str)
        assert '"caption":"Test"' in json_str or '"caption": "Test"' in json_str


class TestScrapeRequest:
    """Tests for ScrapeRequest model"""
    
    def test_scrape_request_creation_valid(self):
        """Test creating valid ScrapeRequest"""
        request = ScrapeRequest(instagram_url="https://www.instagram.com/p/TEST123/")
        assert request.instagram_url == "https://www.instagram.com/p/TEST123/"
    
    def test_scrape_request_validation_missing_url(self):
        """Test ScrapeRequest validation with missing URL"""
        with pytest.raises(ValidationError) as exc_info:
            ScrapeRequest()
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'missing'
        assert 'instagram_url' in error['loc']
    
    def test_scrape_request_validation_empty_url(self):
        """Test ScrapeRequest validation with empty URL"""
        with pytest.raises(ValidationError):
            ScrapeRequest(instagram_url="")
    
    def test_scrape_request_validation_none_url(self):
        """Test ScrapeRequest validation with None URL"""
        with pytest.raises(ValidationError):
            ScrapeRequest(instagram_url=None)
    
    def test_scrape_request_dict_conversion(self):
        """Test converting ScrapeRequest to dictionary"""
        request = ScrapeRequest(instagram_url="https://www.instagram.com/p/TEST123/")
        request_dict = request.dict()
        
        assert isinstance(request_dict, dict)
        assert request_dict['instagram_url'] == "https://www.instagram.com/p/TEST123/"
    
    def test_scrape_request_from_dict(self):
        """Test creating ScrapeRequest from dictionary"""
        data = {"instagram_url": "https://www.instagram.com/p/TEST123/"}
        request = ScrapeRequest(**data)
        
        assert request.instagram_url == "https://www.instagram.com/p/TEST123/"


class TestScrapeResponse:
    """Tests for ScrapeResponse model"""
    
    def test_scrape_response_success(self):
        """Test creating successful ScrapeResponse"""
        post = InstagramPost(caption="Test", type="image")
        response = ScrapeResponse(success=True, data=post)
        
        assert response.success is True
        assert response.data is not None
        assert response.error is None
        assert response.data.caption == "Test"
    
    def test_scrape_response_failure(self):
        """Test creating failed ScrapeResponse"""
        response = ScrapeResponse(success=False, error="Test error message")
        
        assert response.success is False
        assert response.data is None
        assert response.error == "Test error message"
    
    def test_scrape_response_validation_success_required(self):
        """Test ScrapeResponse validation requires success field"""
        with pytest.raises(ValidationError) as exc_info:
            ScrapeResponse()
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'missing'
        assert 'success' in error['loc']
    
    def test_scrape_response_dict_conversion_success(self):
        """Test converting successful ScrapeResponse to dictionary"""
        post = InstagramPost(caption="Test", type="image")
        response = ScrapeResponse(success=True, data=post)
        response_dict = response.dict()
        
        assert isinstance(response_dict, dict)
        assert response_dict['success'] is True
        assert response_dict['data'] is not None
        assert response_dict['error'] is None
    
    def test_scrape_response_dict_conversion_failure(self):
        """Test converting failed ScrapeResponse to dictionary"""
        response = ScrapeResponse(success=False, error="Test error")
        response_dict = response.dict()
        
        assert isinstance(response_dict, dict)
        assert response_dict['success'] is False
        assert response_dict['data'] is None
        assert response_dict['error'] == "Test error"
    
    def test_scrape_response_json_serialization(self):
        """Test JSON serialization of ScrapeResponse"""
        post = InstagramPost(caption="Test", type="image")
        response = ScrapeResponse(success=True, data=post)
        json_str = response.json()
        
        assert isinstance(json_str, str)
        assert '"success":true' in json_str or '"success": true' in json_str
    
    def test_scrape_response_with_null_data(self):
        """Test ScrapeResponse with explicitly null data"""
        response = ScrapeResponse(success=False, data=None, error="Error message")
        
        assert response.success is False
        assert response.data is None
        assert response.error == "Error message"


class TestModelIntegration:
    """Integration tests for models working together"""
    
    def test_full_workflow_models(self):
        """Test models working together in a typical workflow"""
        # Create request
        request = ScrapeRequest(instagram_url="https://www.instagram.com/p/TEST123/")
        
        # Create post data
        post = InstagramPost(
            caption="Test post with #hashtag",
            type="image",
            url=request.instagram_url,
            ownerUsername="testuser",
            hashtags=["hashtag"]
        )
        
        # Create successful response
        success_response = ScrapeResponse(success=True, data=post)
        
        # Verify the workflow
        assert request.instagram_url == post.url
        assert success_response.data.caption == "Test post with #hashtag"
        assert success_response.success is True
        
        # Test serialization
        response_dict = success_response.dict()
        assert response_dict['data']['url'] == request.instagram_url
    
    def test_error_workflow_models(self):
        """Test models in error scenarios"""
        request = ScrapeRequest(instagram_url="https://www.instagram.com/p/PRIVATE/")
        error_response = ScrapeResponse(success=False, error="Private post")
        
        assert error_response.success is False
        assert error_response.data is None
        assert error_response.error == "Private post"


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 