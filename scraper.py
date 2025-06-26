import asyncio
import json
from typing import Optional
from openai import OpenAI
from crawl4ai import AsyncWebCrawler
from models import InstagramPost
from config import Config


class InstagramScraper:
    """Instagram scraper using Crawl4AI and OpenAI for content extraction"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    async def scrape_instagram_post(self, instagram_url: str) -> Optional[InstagramPost]:
        """
        Scrape Instagram post using Crawl4AI and parse with OpenAI
        
        Args:
            instagram_url: Instagram post URL
            
        Returns:
            InstagramPost object with extracted data
        """
        try:
            # Step 1: Scrape content with Crawl4AI
            scraped_content = await self._scrape_with_crawl4ai(instagram_url)
            
            if not scraped_content:
                return None
            
            # Step 2: Parse content with OpenAI structured output
            parsed_data = await self._parse_with_openai(scraped_content, instagram_url)
            
            return parsed_data
            
        except Exception as e:
            print(f"Error scraping Instagram post: {str(e)}")
            return None
    
    async def _scrape_with_crawl4ai(self, url: str) -> Optional[str]:
        """Scrape Instagram post content using Crawl4AI"""
        try:
            async with AsyncWebCrawler(verbose=True) as crawler:
                # Configure crawler for Instagram
                result = await crawler.arun(
                    url=url,
                    # Add headers to appear more like a regular browser
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    },
                    # Wait for dynamic content to load
                    wait_for="css:article",
                    # Extract clean markdown
                    bypass_cache=True
                )
                
                if result.success:
                    return result.markdown
                else:
                    print(f"Crawl4AI failed: {result.error_message}")
                    return None
                    
        except Exception as e:
            print(f"Error with Crawl4AI: {str(e)}")
            return None
    
    async def _parse_with_openai(self, content: str, url: str) -> Optional[InstagramPost]:
        """Parse scraped content using OpenAI with structured output"""
        try:
            # Create the structured output using function calling
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using the latest model
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Instagram post analyzer. 
                        Extract all relevant information from the scraped Instagram post content.
                        
                        Instructions:
                        - Extract the post caption, removing any extra formatting
                        - Identify if it's a video, image, or carousel post
                        - Extract engagement metrics (likes, comments, views)
                        - Find owner information (username, full name)
                        - Extract hashtags and mentions from the caption
                        - Get media URLs if available
                        - Extract timestamp information
                        - Include location if mentioned
                        - Extract alt text for accessibility
                        
                        Be thorough but only include information that is clearly present in the content.
                        Return the data as a JSON object matching the InstagramPost schema.
                        """
                    },
                    {
                        "role": "user",
                        "content": f"""Please analyze this Instagram post content and extract the structured data:

URL: {url}

Content:
{content}

Extract all the available information and return as JSON matching the schema."""
                    }
                ],
                functions=[
                    {
                        "name": "extract_instagram_data",
                        "description": "Extract structured data from Instagram post",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "caption": {"type": "string", "description": "Post caption text"},
                                "type": {"type": "string", "description": "Post type (image, video, carousel)"},
                                "url": {"type": "string", "description": "Original post URL"},
                                "videoUrl": {"type": "string", "description": "Video file URL"},
                                "imageUrl": {"type": "string", "description": "Image file URL"},
                                "displayUrl": {"type": "string", "description": "Display image URL"},
                                "shortCode": {"type": "string", "description": "Instagram post short code"},
                                "timestamp": {"type": "string", "description": "Post creation timestamp"},
                                "likesCount": {"type": "integer", "description": "Number of likes"},
                                "commentsCount": {"type": "integer", "description": "Number of comments"},
                                "videoViewCount": {"type": "integer", "description": "Video view count"},
                                "videoPlayCount": {"type": "integer", "description": "Video play count"},
                                "ownerUsername": {"type": "string", "description": "Account username"},
                                "ownerFullName": {"type": "string", "description": "Account full name"},
                                "locationName": {"type": "string", "description": "Location tag"},
                                "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Array of hashtags"},
                                "mentions": {"type": "array", "items": {"type": "string"}, "description": "Array of mentioned users"},
                                "alt": {"type": "string", "description": "Alt text for accessibility"}
                            }
                        }
                    }
                ],
                function_call={"name": "extract_instagram_data"}
            )
            
            if response.choices[0].message.function_call:
                import json
                function_args = json.loads(response.choices[0].message.function_call.arguments)
                return InstagramPost(**function_args)
            else:
                print("No function call response from OpenAI")
                return None
            
        except Exception as e:
            print(f"Error parsing with OpenAI: {str(e)}")
            return None 