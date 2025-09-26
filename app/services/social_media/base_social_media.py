"""
Base social media API service implementation
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.interfaces import ISocialMediaAPIService, SocialMediaMetrics, TrendingContent

logger = logging.getLogger(__name__)


class BaseSocialMediaAPIService(ISocialMediaAPIService):
    """Base implementation for social media API services"""
    
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        self.api_key = api_key
        self.access_token = access_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_info = {
            "requests_per_hour": 300,
            "current_requests": 0,
            "last_reset": datetime.now()
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'User-Agent': 'ViralTogether/1.0 (AI Agent System)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    async def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request with rate limiting"""
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")
        
        # Check rate limits
        await self._check_rate_limit()
        
        logger.info(f"Making HTTP request to: {url} with params: {params}")
        try:
            async with self.session.get(url, params=params) as response:
                logger.info(f"HTTP response status: {response.status} for {url}")
                if response.status == 429:  # Rate limited
                    logger.warning("Rate limited, waiting before retry")
                    await asyncio.sleep(60)
                    return await self._make_request(url, params)
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in social media API: {e}")
            raise
    
    async def _check_rate_limit(self):
        """Check and update rate limits"""
        now = datetime.now()
        
        # Reset hourly counter if needed
        if (now - self.rate_limit_info["last_reset"]).seconds >= 3600:
            self.rate_limit_info["current_requests"] = 0
            self.rate_limit_info["last_reset"] = now
        
        # Check if we're over the limit
        if self.rate_limit_info["current_requests"] >= self.rate_limit_info["requests_per_hour"]:
            raise Exception("Hourly rate limit exceeded")
        
        self.rate_limit_info["current_requests"] += 1
    
    def _parse_metrics(self, data: Dict[str, Any]) -> SocialMediaMetrics:
        """Parse API response into standardized metrics"""
        return SocialMediaMetrics(
            platform=self._get_platform_name(),
            followers=data.get('followers_count', 0),
            engagement_rate=data.get('engagement_rate', 0.0),
            reach=data.get('reach', 0),
            impressions=data.get('impressions', 0),
            likes=data.get('likes', 0),
            comments=data.get('comments', 0),
            shares=data.get('shares', 0),
            timestamp=datetime.now()
        )
    
    def _parse_trending_content(self, data: Dict[str, Any]) -> List[TrendingContent]:
        """Parse trending content from API response"""
        trending = []
        
        for item in data.get('trends', []):
            trending.append(TrendingContent(
                platform=self._get_platform_name(),
                hashtag=item.get('hashtag', ''),
                post_count=item.get('post_count', 0),
                engagement_rate=item.get('engagement_rate', 0.0),
                trend_score=item.get('trend_score', 0.0),
                category=item.get('category', 'general'),
                timestamp=datetime.now()
            ))
        
        return trending
    
    def _get_platform_name(self) -> str:
        """Get platform name - to be overridden by subclasses"""
        return "unknown"
    
    async def get_user_metrics(self, username: str) -> SocialMediaMetrics:
        """Base implementation - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement get_user_metrics method")
    
    async def get_trending_hashtags(self, platform: str, limit: int = 20) -> List[TrendingContent]:
        """Base implementation - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement get_trending_hashtags method")
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Base implementation - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement get_post_analytics method")
    
    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Base implementation - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement search_posts method")
