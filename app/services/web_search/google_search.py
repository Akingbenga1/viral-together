"""
Google Custom Search service implementation
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.web_search.base_web_search import BaseWebSearchService
from app.core.interfaces import SearchResult

logger = logging.getLogger(__name__)


class GoogleSearchService(BaseWebSearchService):
    """Google Custom Search service implementation"""
    
    def __init__(self, api_key: str, search_engine_id: str):
        super().__init__(api_key=api_key)
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.rate_limit_info = {
            "requests_per_day": 100,  # Free tier limit
            "current_requests": 0,
            "last_reset": datetime.now()
        }
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': min(max_results, 10),  # Google API limit
            'safe': 'medium',
            'fields': 'items(title,link,snippet,pagemap)'
        }
        
        try:
            data = await self._make_request(self.base_url, params)
            return self._parse_google_results(data)
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
    
    def _parse_google_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse Google Custom Search API response"""
        results = []
        
        for item in data.get('items', []):
            try:
                # Extract publication date if available
                published_date = None
                if 'pagemap' in item and 'metatags' in item['pagemap']:
                    for meta in item['pagemap']['metatags']:
                        if 'article:published_time' in meta:
                            published_date = self._parse_date(meta['article:published_time'])
                            break
                
                result = SearchResult(
                    title=item.get('title', ''),
                    snippet=item.get('snippet', ''),
                    url=item.get('link', ''),
                    published_date=published_date,
                    source='Google Custom Search'
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse Google search result: {e}")
                continue
        
        return results
    
    async def search_trends(self, topic: str, timeframe: str = "7d") -> List[SearchResult]:
        """Search for trending information"""
        trend_queries = [
            f'"{topic}" trending 2024',
            f'"{topic}" viral content',
            f'"{topic}" popular posts',
            f'"{topic}" latest trends'
        ]
        
        all_results = []
        for query in trend_queries:
            results = await self.search(query, max_results=3)
            all_results.extend(results)
        
        return all_results[:10]
    
    async def search_news(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search for recent news"""
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': f'"{query}" news',
            'num': min(max_results, 10),
            'safe': 'medium',
            'sort': 'date',
            'fields': 'items(title,link,snippet,pagemap)'
        }
        
        try:
            data = await self._make_request(self.base_url, params)
            return self._parse_google_results(data)
        except Exception as e:
            logger.error(f"Google news search failed: {e}")
            return []
