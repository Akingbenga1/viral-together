"""
DuckDuckGo search service implementation using the duckduckgo-search library
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.web_search.base_web_search import BaseWebSearchService
from app.core.interfaces import SearchResult

# Import duckduckgo_search library
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
    logging.warning("duckduckgo-search not installed. Run: pip install duckduckgo-search")

logger = logging.getLogger(__name__)


class DuckDuckGoSearchService(BaseWebSearchService):
    """DuckDuckGo search service implementation using ddg_maps for business search"""
    
    def __init__(self):
        super().__init__()
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search using DuckDuckGo Maps for businesses
        This is the main method called by the search service
        """
        try:
            logger.info(f"Searching DuckDuckGo Maps for: {query}")
            
            if DDGS is None:
                logger.error("duckduckgo-search library not available")
                return []
            
            # Use DuckDuckGo Maps search (synchronous, so run in executor)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self._search_maps_sync, 
                query, 
                max_results
            )
            
            if results:
                logger.info(f"Found {len(results)} DuckDuckGo Maps results")
            else:
                logger.warning(f"No results found for query: {query}")
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}", exc_info=True)
            return []
    
    def _search_maps_sync(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Synchronous Maps search using ddg_maps
        This must be sync because the DDGS library is synchronous
        """
        results = []
        try:
            with DDGS() as ddgs:
                # Search using maps - this returns locations/businesses
                for result in ddgs.maps(query, max_results=max_results):
                    # Parse the result into our SearchResult format
                    search_result = SearchResult(
                        title=result.get('title', 'Unknown Business'),
                        snippet=result.get('body', '').replace('\n', ' ')[:200],
                        url=result.get('website', ''),
                        source='DuckDuckGo Maps'
                    )
                    results.append(search_result)
                    
                    if len(results) >= max_results:
                        break
            
            logger.info(f"Retrieved {len(results)} results from DuckDuckGo Maps")
            
        except Exception as e:
            logger.error(f"DuckDuckGo Maps search failed: {str(e)}")
        
        return results
    
    async def search_maps_with_location(
        self, 
        keywords: str, 
        city: str, 
        country: str, 
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search DuckDuckGo Maps with specific city and country
        This is more targeted for business searches by location
        """
        try:
            if DDGS is None:
                logger.error("duckduckgo-search library not available")
                return []
            
            logger.info(f"Searching DuckDuckGo Maps for '{keywords}' in {city}, {country}")
            
            # Build search query with location
            query = f"{keywords} {city} {country}"
            
            # Use the main search method which calls Maps
            results = await self.search(query, max_results=max_results)
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo Maps location search failed: {e}")
            return []
    
    async def search_trends(self, topic: str, timeframe: str = "7d") -> List[SearchResult]:
        """Search for trending information with DuckDuckGo"""
        trend_queries = [
            f"{topic} trending now",
            f"{topic} viral content",
            f"{topic} popular posts",
            f"{topic} latest trends"
        ]
        
        all_results = []
        for query in trend_queries:
            results = await self.search(query, max_results=3)
            all_results.extend(results)
        
        return all_results[:10]
    
    async def search_news(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search for recent news"""
        news_query = f"{query} news recent"
        return await self.search(news_query, max_results=max_results)
