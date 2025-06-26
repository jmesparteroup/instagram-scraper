from pydantic import BaseModel
from typing import Optional, List


class InstagramPost(BaseModel):
    """Instagram post data structure"""
    caption: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    videoUrl: Optional[str] = None
    imageUrl: Optional[str] = None
    displayUrl: Optional[str] = None
    shortCode: Optional[str] = None
    timestamp: Optional[str] = None
    likesCount: Optional[int] = None
    commentsCount: Optional[int] = None
    videoViewCount: Optional[int] = None
    videoPlayCount: Optional[int] = None
    ownerUsername: Optional[str] = None
    ownerFullName: Optional[str] = None
    locationName: Optional[str] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    alt: Optional[str] = None


class ScrapeRequest(BaseModel):
    """Request model for Instagram scraping"""
    instagram_url: str


class ScrapeResponse(BaseModel):
    """Response model for Instagram scraping"""
    success: bool
    data: Optional[InstagramPost] = None
    error: Optional[str] = None 