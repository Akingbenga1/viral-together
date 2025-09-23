"""
Social media API service factory for creating different platform providers
"""

from typing import Optional
from app.core.interfaces import ISocialMediaAPIService
from app.services.social_media.twitter_api import TwitterAPIService
from app.services.social_media.instagram_api import InstagramAPIService
from app.services.social_media.youtube_api import YouTubeAPIService
from app.services.social_media.tiktok_api import TikTokAPIService
from app.core.config import settings


class SocialMediaFactory:
    """Factory for creating social media API services"""
    
    @staticmethod
    def create_social_media_service(platform: str, **kwargs) -> ISocialMediaAPIService:
        """
        Create a social media API service based on the platform
        
        Args:
            platform: Social media platform ("twitter", "instagram", "youtube", "tiktok")
            **kwargs: Additional configuration parameters
        
        Returns:
            ISocialMediaAPIService: Configured social media service
        """
        platform = platform.lower()
        
        if platform == "twitter":
            bearer_token = kwargs.get('bearer_token') or settings.TWITTER_BEARER_TOKEN
            if not bearer_token:
                raise ValueError("Twitter service requires bearer token")
            return TwitterAPIService(bearer_token=bearer_token)
        
        elif platform == "instagram":
            access_token = kwargs.get('access_token') or settings.INSTAGRAM_ACCESS_TOKEN
            if not access_token:
                raise ValueError("Instagram service requires access token")
            return InstagramAPIService(access_token=access_token)
        
        elif platform == "youtube":
            api_key = kwargs.get('api_key') or settings.YOUTUBE_API_KEY
            if not api_key:
                raise ValueError("YouTube service requires API key")
            return YouTubeAPIService(api_key=api_key)
        
        elif platform == "tiktok":
            access_token = kwargs.get('access_token') or settings.TIKTOK_ACCESS_TOKEN
            if not access_token:
                raise ValueError("TikTok service requires access token")
            return TikTokAPIService(access_token=access_token)
        
        else:
            raise ValueError(f"Unsupported social media platform: {platform}")
    
    @staticmethod
    def get_available_platforms() -> list:
        """Get list of available social media platforms"""
        return ["twitter", "instagram", "youtube", "tiktok"]
    
    @staticmethod
    def get_platform_requirements(platform: str) -> dict:
        """Get requirements for a specific platform"""
        requirements = {
            "twitter": {
                "required": ["bearer_token"],
                "optional": ["api_key", "api_secret"],
                "description": "Twitter API v2 with Bearer Token"
            },
            "instagram": {
                "required": ["access_token"],
                "optional": ["app_id", "app_secret"],
                "description": "Instagram Basic Display API"
            },
            "youtube": {
                "required": ["api_key"],
                "optional": ["client_id", "client_secret"],
                "description": "YouTube Data API v3"
            },
            "tiktok": {
                "required": ["access_token"],
                "optional": ["client_key", "client_secret"],
                "description": "TikTok for Business API"
            }
        }
        
        return requirements.get(platform.lower(), {})
