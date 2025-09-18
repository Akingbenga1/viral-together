"""
DuckDuckGo search service implementation using free API
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus
from app.services.web_search.base_web_search import BaseWebSearchService
from app.core.interfaces import SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoSearchService(BaseWebSearchService):
    """DuckDuckGo search service implementation"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.duckduckgo.com"
        self.instant_answer_url = "https://api.duckduckgo.com/"
        self.html_search_url = "https://html.duckduckgo.com/html/"
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo API"""
        try:
            # Try instant answer API first
            instant_results = await self._search_instant_answer(query)
            
            if instant_results:
                return instant_results[:max_results]
            
            # Fallback to HTML scraping (for more comprehensive results)
            html_results = await self._search_html(query, max_results)
            return html_results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def _search_instant_answer(self, query: str) -> List[SearchResult]:
        """Search using DuckDuckGo instant answer API"""
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.instant_answer_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_instant_answer(data, query)
        except Exception as e:
            logger.warning(f"Instant answer search failed: {e}")
        
        return []
    
    async def _search_html(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo HTML interface (fallback)"""
        params = {
            'q': query,
            'kl': 'us-en'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.html_search_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_html_results(html, max_results)
        except Exception as e:
            logger.warning(f"HTML search failed: {e}")
        
        return []
    
    def _parse_instant_answer(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse instant answer API response"""
        results = []
        
        # Abstract text
        if data.get('Abstract'):
            results.append(SearchResult(
                title=data.get('Heading', query),
                snippet=data.get('Abstract', ''),
                url=data.get('AbstractURL', ''),
                source='DuckDuckGo Instant Answer'
            ))
        
        # Related topics
        for topic in data.get('RelatedTopics', []):
            if isinstance(topic, dict) and topic.get('Text'):
                results.append(SearchResult(
                    title=topic.get('FirstURL', '').split('/')[-1] if topic.get('FirstURL') else 'Related Topic',
                    snippet=topic.get('Text', ''),
                    url=topic.get('FirstURL', ''),
                    source='DuckDuckGo Related Topics'
                ))
        
        return results
    
    def _parse_html_results(self, html: str, max_results: int) -> List[SearchResult]:
        """Parse HTML search results (simplified implementation)"""
        results = []
        
        # This is a simplified HTML parser
        # In a production environment, you'd use BeautifulSoup or similar
        import re
        
        # Extract result links and snippets
        link_pattern = r'<a[^>]+href="([^"]+)"[^>]*class="result__a"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<a[^>]+class="result__snippet"[^>]*>([^<]+)</a>'
        
        links = re.findall(link_pattern, html)
        snippets = re.findall(snippet_pattern, html)
        
        for i, (url, title) in enumerate(links[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ''
            
            # Clean up the URL
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = 'https://duckduckgo.com' + url
            
            results.append(SearchResult(
                title=title.strip(),
                snippet=snippet.strip(),
                url=url,
                source='DuckDuckGo HTML Search'
            ))
        
        return results
    
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
