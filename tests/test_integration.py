"""
Integration tests for different Instagram post types and scenarios
"""

import pytest
from unittest.mock import patch, Mock
from models import InstagramPost


class TestPostTypeIntegration:
    """Integration tests for different Instagram post types"""
    
    @pytest.mark.parametrize("post_type,test_url,expected_fields", [
        (
            "image", 
            "https://www.instagram.com/p/IMG123/",
            {"type": "image", "imageUrl": "test_image.jpg", "displayUrl": "test_display.jpg"}
        ),
        (
            "video", 
            "https://www.instagram.com/p/VID456/",
            {"type": "video", "videoUrl": "test_video.mp4", "videoViewCount": 1000}
        ),
        (
            "carousel", 
            "https://www.instagram.com/p/CAR789/",
            {"type": "carousel", "imageUrl": "carousel_1.jpg"}
        ),
    ])
    def test_api_different_post_types(self, client, post_type, test_url, expected_fields):
        """Test API with different Instagram post types"""
        # Create mock post data for specific type
        post_data = InstagramPost(
            caption=f"Test {post_type} post with #hashtag",
            type=post_type,
            url=test_url,
            shortCode=test_url.split('/')[-2],
            ownerUsername="testuser",
            hashtags=["hashtag"]
        )
        
        # Add type-specific fields
        for field, value in expected_fields.items():
            setattr(post_data, field, value)
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = post_data
            
            response = client.post('/scrape', 
                json={'instagram_url': test_url},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert data['data']['type'] == post_type
            assert data['data']['url'] == test_url
            
            # Verify type-specific fields
            for field, expected_value in expected_fields.items():
                if field != 'type':  # type is already checked above
                    assert data['data'][field] == expected_value


class TestErrorScenariosIntegration:
    """Integration tests for various error scenarios"""
    
    @pytest.mark.parametrize("error_type,error_message,expected_status,expected_error_pattern", [
        (
            "private_post",
            "Instagram post is private or access denied",
            404,
            "private"
        ),
        (
            "deleted_post", 
            "Instagram post not found or deleted",
            404,
            "not found"
        ),
        (
            "rate_limited",
            "Instagram is rate limiting requests", 
            429,
            "rate limiting"
        ),
        (
            "openai_quota",
            "OpenAI API quota exceeded or billing issue",
            503,
            "AI processing service"
        ),
        (
            "network_error",
            "Network error occurred",
            503,
            "Network error"
        )
    ])
    def test_api_error_scenarios(self, client, error_type, error_message, expected_status, expected_error_pattern):
        """Test API error handling for different scenarios"""
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.side_effect = Exception(error_message)
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TEST123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == expected_status
            data = response.get_json()
            assert data['success'] is False
            assert expected_error_pattern.lower() in data['error'].lower()


class TestRealWorldScenarios:
    """Tests simulating real-world Instagram scraping scenarios"""
    
    def test_complete_image_post_extraction(self, client):
        """Test complete extraction of an image post with all fields"""
        complete_post = InstagramPost(
            caption="Beautiful sunset 🌅 #sunset #photography #nature",
            type="image",
            url="https://www.instagram.com/p/SUNSET123/",
            imageUrl="https://instagram.com/sunset.jpg",
            displayUrl="https://instagram.com/sunset_display.jpg",
            shortCode="SUNSET123",
            timestamp="2024-01-15T18:30:00Z",
            likesCount=2547,
            commentsCount=128,
            ownerUsername="photographer_jane",
            ownerFullName="Jane Smith Photography",
            locationName="Malibu Beach, California",
            hashtags=["sunset", "photography", "nature"],
            mentions=[],
            alt="Beautiful sunset over the ocean with vibrant orange and pink colors"
        )
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = complete_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/SUNSET123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify all fields are correctly extracted
            post_data = data['data']
            assert post_data['caption'] == "Beautiful sunset 🌅 #sunset #photography #nature"
            assert post_data['type'] == "image"
            assert post_data['likesCount'] == 2547
            assert post_data['commentsCount'] == 128
            assert post_data['ownerUsername'] == "photographer_jane"
            assert post_data['locationName'] == "Malibu Beach, California"
            assert post_data['hashtags'] == ["sunset", "photography", "nature"]
            assert post_data['alt'] == "Beautiful sunset over the ocean with vibrant orange and pink colors"
    
    def test_complete_video_post_extraction(self, client):
        """Test complete extraction of a video post with video-specific fields"""
        video_post = InstagramPost(
            caption="Check out this amazing dance routine! 💃 @dancestudio #dance #choreography",
            type="video",
            url="https://www.instagram.com/p/DANCE456/",
            videoUrl="https://instagram.com/dance_video.mp4",
            displayUrl="https://instagram.com/dance_thumbnail.jpg",
            shortCode="DANCE456",
            timestamp="2024-01-15T20:15:00Z",
            likesCount=15230,
            commentsCount=892,
            videoViewCount=45720,
            videoPlayCount=43891,
            ownerUsername="dance_crew_official",
            ownerFullName="Professional Dance Crew",
            hashtags=["dance", "choreography"],
            mentions=["dancestudio"],
            alt="Professional dancers performing contemporary choreography in a studio"
        )
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = video_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/DANCE456/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify video-specific fields
            post_data = data['data']
            assert post_data['type'] == "video"
            assert post_data['videoUrl'] == "https://instagram.com/dance_video.mp4"
            assert post_data['videoViewCount'] == 45720
            assert post_data['videoPlayCount'] == 43891
            assert post_data['mentions'] == ["dancestudio"]
    
    def test_carousel_post_extraction(self, client):
        """Test extraction of a carousel post (multiple images)"""
        carousel_post = InstagramPost(
            caption="Travel memories from Europe 🇪🇺 Swipe to see all photos! #travel #europe #memories",
            type="carousel",
            url="https://www.instagram.com/p/TRAVEL789/",
            imageUrl="https://instagram.com/europe_1.jpg",  # First image in carousel
            displayUrl="https://instagram.com/europe_display.jpg",
            shortCode="TRAVEL789",
            timestamp="2024-01-10T14:22:00Z",
            likesCount=3456,
            commentsCount=234,
            ownerUsername="world_traveler",
            ownerFullName="Travel Enthusiast",
            locationName="Paris, France",
            hashtags=["travel", "europe", "memories"],
            mentions=[],
            alt="Collection of travel photos from various European cities"
        )
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = carousel_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/TRAVEL789/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify carousel-specific handling
            post_data = data['data']
            assert post_data['type'] == "carousel"
            assert post_data['locationName'] == "Paris, France"
            assert "Swipe to see" in post_data['caption']


class TestEdgeCases:
    """Tests for edge cases and unusual scenarios"""
    
    def test_post_with_no_engagement(self, client):
        """Test post with zero likes and comments"""
        minimal_post = InstagramPost(
            caption="Just posted this",
            type="image",
            url="https://www.instagram.com/p/MINIMAL123/",
            shortCode="MINIMAL123",
            likesCount=0,
            commentsCount=0,
            ownerUsername="new_user"
        )
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = minimal_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/MINIMAL123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['likesCount'] == 0
            assert data['data']['commentsCount'] == 0
    
    def test_post_with_special_characters(self, client):
        """Test post with emojis and special characters"""
        emoji_post = InstagramPost(
            caption="Amazing day! 🌟✨🎉 #blessed 🙏 @friend 👫",
            type="image", 
            url="https://www.instagram.com/p/EMOJI123/",
            shortCode="EMOJI123",
            ownerUsername="emoji_lover",
            hashtags=["blessed"],
            mentions=["friend"]
        )
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = emoji_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/EMOJI123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify emojis and special characters are preserved
            caption = data['data']['caption']
            assert "🌟" in caption
            assert "✨" in caption
            assert "🎉" in caption
            assert data['data']['hashtags'] == ["blessed"]
            assert data['data']['mentions'] == ["friend"]
    
    def test_post_with_very_long_caption(self, client):
        """Test post with extremely long caption"""
        long_caption = "This is a very long caption. " * 50  # 1500+ characters
        long_caption += "#test #long #caption"
        
        long_post = InstagramPost(
            caption=long_caption,
            type="image",
            url="https://www.instagram.com/p/LONG123/",
            shortCode="LONG123",
            ownerUsername="verbose_user",
            hashtags=["test", "long", "caption"]
        )
        
        with patch('scraper.InstagramScraper.scrape_instagram_post') as mock_scrape:
            mock_scrape.return_value = long_post
            
            response = client.post('/scrape', 
                json={'instagram_url': 'https://www.instagram.com/p/LONG123/'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['data']['caption']) > 1500
            assert data['data']['hashtags'] == ["test", "long", "caption"]


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 