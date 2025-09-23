"""
Base web search service implementation
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.interfaces import IWebSearchService, SearchResult

logger = logging.getLogger(__name__)


class BaseWebSearchService(IWebSearchService):
    """Base implementation for web search services"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_info = {
            "requests_per_minute": 60,
            "requests_per_day": 1000,
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
        
        return headers
    
    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with rate limiting"""
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")
        
        # Check rate limits
        await self._check_rate_limit()
        
        try:
            async with self.session.get(url, params=params) as response:
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
            logger.error(f"Unexpected error in web search: {e}")
            raise
    
    async def _check_rate_limit(self):
        """Check and update rate limits"""
        now = datetime.now()
        
        # Reset daily counter if needed
        if (now - self.rate_limit_info["last_reset"]).days >= 1:
            self.rate_limit_info["current_requests"] = 0
            self.rate_limit_info["last_reset"] = now
        
        # Check if we're over the limit
        if self.rate_limit_info["current_requests"] >= self.rate_limit_info["requests_per_day"]:
            raise Exception("Daily rate limit exceeded")
        
        self.rate_limit_info["current_requests"] += 1
    
    def _parse_search_results(self, raw_results: List[Dict[str, Any]]) -> List[SearchResult]:
        """Parse raw search results into standardized format"""
        results = []
        
        for item in raw_results:
            try:
                result = SearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('snippet', ''),
                    url=item.get('url', ''),
                    published_date=self._parse_date(item.get('published_date')),
                    relevance_score=item.get('relevance_score'),
                    source=item.get('source')
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse search result: {e}")
                continue
        
        return results
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        
        return None
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Base search implementation - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement search method")
    
    async def search_trends(self, topic: str, timeframe: str = "7d") -> List[SearchResult]:
        """Search for trending information about a topic"""
        trend_query = f"{topic} trends {timeframe} influencer marketing"
        return await self.search(trend_query, max_results=10)
    
    async def search_news(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search for recent news about a topic"""
        news_query = f"{query} news recent influencer marketing"
        return await self.search(news_query, max_results=max_results)
