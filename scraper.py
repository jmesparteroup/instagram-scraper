import asyncio
import json
import logging
import time
from typing import Optional
from openai import OpenAI
from crawl4ai import AsyncWebCrawler
from models import InstagramPost
from config import Config

logger = logging.getLogger(__name__)

class InstagramScraper:
    """Instagram scraper using Crawl4AI and OpenAI for content extraction"""
    
    def __init__(self):
        self.openai_client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=Config.OPENAI_TIMEOUT
        )
        logger.info("Instagram scraper initialized")
    
    async def scrape_instagram_post(self, instagram_url: str) -> Optional[InstagramPost]:
        """
        Scrape Instagram post using Crawl4AI and parse with OpenAI
        
        Args:
            instagram_url: Instagram post URL
            
        Returns:
            InstagramPost object with extracted data
            
        Raises:
            Exception: Various exceptions for different error conditions
        """
        logger.info(f"Starting scrape for URL: {instagram_url}")
        
        try:
            # Step 1: Scrape content with Crawl4AI (with retries)
            scraped_content = await self._scrape_with_crawl4ai_retry(instagram_url)
            
            if not scraped_content:
                logger.error(f"Failed to scrape content from {instagram_url}")
                raise Exception("Failed to retrieve content from Instagram")
            
            logger.info(f"Successfully scraped content, length: {len(scraped_content)} characters")
            
            # Step 2: Parse content with OpenAI structured output
            parsed_data = await self._parse_with_openai(scraped_content, instagram_url)
            
            if not parsed_data:
                logger.error(f"Failed to parse content for {instagram_url}")
                raise Exception("Failed to parse Instagram content")
            
            logger.info(f"Successfully parsed Instagram post: {parsed_data.ownerUsername or 'unknown'}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error scraping Instagram post {instagram_url}: {str(e)}")
            raise
    
    async def _scrape_with_crawl4ai_retry(self, url: str) -> Optional[str]:
        """Scrape Instagram post content with retry logic"""
        for attempt in range(Config.INSTAGRAM_MAX_RETRIES):
            try:
                logger.info(f"Scraping attempt {attempt + 1}/{Config.INSTAGRAM_MAX_RETRIES} for {url}")
                
                content = await self._scrape_with_crawl4ai(url)
                if content:
                    return content
                
                if attempt < Config.INSTAGRAM_MAX_RETRIES - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {Config.INSTAGRAM_RETRY_DELAY}s")
                    await asyncio.sleep(Config.INSTAGRAM_RETRY_DELAY)
                
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed: {str(e)}")
                if attempt < Config.INSTAGRAM_MAX_RETRIES - 1:
                    await asyncio.sleep(Config.INSTAGRAM_RETRY_DELAY)
                else:
                    raise
        
        return None
    
    async def _scrape_with_crawl4ai(self, url: str) -> Optional[str]:
        """Scrape Instagram post content using Crawl4AI"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                # Configure crawler for Instagram with enhanced settings for video content
                result = await crawler.arun(
                    url=url,
                    # Enhanced headers to appear more like a regular browser
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,video/webm,video/mp4,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0'
                    },
                    # Wait for dynamic content to load, including video elements
                    wait_for="css:article,video,source,[data-testid]",
                    # Additional settings for better video content scraping
                    bypass_cache=True,
                    page_timeout=45000,  # 45 seconds for video loading
                    delay_before_return_html=3000,  # 3 seconds delay for video elements
                    # Enable media extraction to capture video URLs
                    extract_media=True,
                    # Extract structured content including media URLs
                    extract_structured=True,
                )
                
                if result.success:
                    if not result.markdown or len(result.markdown.strip()) < 100:
                        logger.warning(f"Retrieved content is too short or empty for {url}")
                        return None
                    
                    # Include extracted media URLs in the content for better video detection
                    content_with_media = result.markdown
                    if hasattr(result, 'media') and result.media:
                        media_info = "\n\n--- EXTRACTED MEDIA URLS ---\n"
                        for media_item in result.media:
                            if hasattr(media_item, 'url') and media_item.url:
                                media_type = getattr(media_item, 'type', 'unknown')
                                media_info += f"Media URL ({media_type}): {media_item.url}\n"
                        content_with_media += media_info
                    
                    logger.debug(f"Crawl4AI successful for {url}")
                    return content_with_media
                else:
                    error_msg = result.error_message or "Unknown error"
                    logger.error(f"Crawl4AI failed for {url}: {error_msg}")
                    
                    # Categorize errors for better handling
                    if "404" in error_msg or "not found" in error_msg.lower():
                        raise Exception("Instagram post not found or deleted")
                    elif "403" in error_msg or "forbidden" in error_msg.lower():
                        raise Exception("Instagram post is private or access denied")
                    elif "rate limit" in error_msg.lower() or "429" in error_msg:
                        raise Exception("Instagram is rate limiting requests")
                    else:
                        raise Exception(f"Failed to access Instagram post: {error_msg}")
                    
        except Exception as e:
            logger.error(f"Error with Crawl4AI for {url}: {str(e)}")
            raise
    
    async def _parse_with_openai(self, content: str, url: str) -> Optional[InstagramPost]:
        """Parse scraped content using OpenAI with structured output"""
        try:
            logger.info(f"Starting OpenAI parsing for {url}")
            
            # Create the structured output using function calling
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using the latest model
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Instagram post analyzer. 
                        Extract all relevant information from the scraped Instagram post content.
                        
                        CRITICAL PRIORITY: VIDEO CONTENT DETECTION
                        - ALWAYS prioritize video URLs over image URLs when both are available
                        - Look for video-specific indicators: .mp4, .mov, video/, video tags, play buttons, duration, video views
                        - If ANY video content is found (reels, videos, IGTV), set type as "video" and prioritize videoUrl
                        - Only use "image" type if NO video content is detected anywhere in the post
                        
                        Instructions:
                        - Extract the post caption, removing any extra formatting
                        - Identify post type with VIDEO PRIORITY: "video" for any video content (reels/videos/IGTV), "carousel" for multiple items, "image" only if no video
                        - Extract engagement metrics (likes, comments, views) if visible
                        - Find owner information (username, full name)
                        - Extract hashtags (words starting with #) and mentions (words starting with @) from the caption
                        - Get media URLs with VIDEO PRIORITY: search for video URLs first (.mp4, .mov, video/, streaming URLs)
                        - Extract timestamp information if available
                        - Include location if mentioned
                        - Extract alt text for accessibility if present
                        
                        VIDEO URL DETECTION PRIORITY:
                        1. Look for direct video file URLs (.mp4, .mov, .webm)
                        2. Look for streaming video URLs (contains 'video' in path)
                        3. Look for Instagram video CDN URLs
                        4. Only fall back to image URLs if no video is found
                        
                        Be thorough but only include information that is clearly present in the content.
                        If information is not available, leave the field as null.
                        Return accurate data based on what you can extract from the content.
                        """
                    },
                    {
                        "role": "user",
                        "content": f"""Please analyze this Instagram post content and extract the structured data:

URL: {url}

Content:
{content[:4000]}  # Limit content to avoid token limits

Extract all the available information and return as JSON matching the schema. Focus on accuracy over completeness."""
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
                                "videoUrl": {"type": "string", "description": "Video file URL - PRIORITIZE THIS over imageUrl if any video content exists (.mp4, .mov, video/, streaming URLs)"},
                                "imageUrl": {"type": "string", "description": "Image file URL - ONLY use if no video content is available"},
                                "displayUrl": {"type": "string", "description": "Display image URL if available"},
                                "shortCode": {"type": "string", "description": "Instagram post short code from URL"},
                                "timestamp": {"type": "string", "description": "Post creation timestamp if available"},
                                "likesCount": {"type": "integer", "description": "Number of likes if visible"},
                                "commentsCount": {"type": "integer", "description": "Number of comments if visible"},
                                "videoViewCount": {"type": "integer", "description": "Video view count if available"},
                                "videoPlayCount": {"type": "integer", "description": "Video play count if available"},
                                "ownerUsername": {"type": "string", "description": "Account username"},
                                "ownerFullName": {"type": "string", "description": "Account full name if available"},
                                "locationName": {"type": "string", "description": "Location tag if present"},
                                "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Array of hashtags (without #) from caption"},
                                "mentions": {"type": "array", "items": {"type": "string"}, "description": "Array of mentioned users (without @) from caption"},
                                "alt": {"type": "string", "description": "Alt text for accessibility if present"}
                            }
                        }
                    }
                ],
                function_call={"name": "extract_instagram_data"},
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1500
            )
            
            if response.choices[0].message.function_call:
                function_args = json.loads(response.choices[0].message.function_call.arguments)
                
                # Add the original URL if not present
                if not function_args.get('url'):
                    function_args['url'] = url
                
                # Extract shortCode from URL if not extracted
                if not function_args.get('shortCode') and '/p/' in url:
                    import re
                    match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
                    if match:
                        function_args['shortCode'] = match.group(1)
                
                logger.info(f"OpenAI parsing successful for {url}")
                
                # Post-process to ensure video prioritization
                post_data = self._prioritize_video_content(InstagramPost(**function_args))
                return post_data
            else:
                logger.error(f"No function call response from OpenAI for {url}")
                raise Exception("OpenAI failed to parse Instagram content")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from OpenAI response for {url}: {str(e)}")
            raise Exception("Failed to parse OpenAI response")
        except Exception as e:
            logger.error(f"Error parsing with OpenAI for {url}: {str(e)}")
            # Check for OpenAI specific errors
            error_msg = str(e).lower()
            if "api key" in error_msg:
                raise Exception("OpenAI API key is invalid or missing")
            elif "quota" in error_msg or "billing" in error_msg:
                raise Exception("OpenAI API quota exceeded or billing issue")
            elif "rate limit" in error_msg:
                raise Exception("OpenAI API rate limit exceeded")
            else:
                raise Exception(f"OpenAI processing failed: {str(e)}")
    
    def _prioritize_video_content(self, post: InstagramPost) -> InstagramPost:
        """
        Post-process Instagram post data to ensure video content is prioritized
        """
        # If we have a video URL, ensure the type is set to video
        if post.videoUrl and post.videoUrl.strip():
            # Check if the URL looks like a video file
            video_extensions = ['.mp4', '.mov', '.webm', '.avi']
            video_indicators = ['video/', '/video', 'videos.', 'videoplayback']
            
            video_url_lower = post.videoUrl.lower()
            is_video_url = (
                any(ext in video_url_lower for ext in video_extensions) or
                any(indicator in video_url_lower for indicator in video_indicators)
            )
            
            if is_video_url:
                # Force type to video and log the prioritization
                logger.info(f"Video URL detected, setting type to 'video': {post.videoUrl}")
                post.type = "video"
                
                # If we only have an image URL but detected video, clear the image URL
                # to avoid confusion (video should be primary)
                if post.imageUrl and not post.displayUrl:
                    post.displayUrl = post.imageUrl  # Keep as thumbnail
                    post.imageUrl = None  # Clear primary image URL
        
        # If we have video view counts but no type, it's likely a video
        if (post.videoViewCount or post.videoPlayCount) and not post.type:
            logger.info("Video view counts detected, setting type to 'video'")
            post.type = "video"
        
        # Log final media URLs for debugging
        logger.debug(f"Final media URLs - Video: {post.videoUrl}, Image: {post.imageUrl}, Display: {post.displayUrl}")
        
        return post 