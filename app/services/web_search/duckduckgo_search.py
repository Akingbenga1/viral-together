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
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            # Try HTML search first (more reliable)
            html_results = await self._search_html(query, max_results)
            if html_results:
                logger.info(f"Found {len(html_results)} HTML results")
                return html_results
            
            # Fallback to instant answer API
            instant_results = await self._search_instant_answer(query)
            if instant_results:
                logger.info(f"Found {len(instant_results)} instant answer results")
                return instant_results[:max_results]
            
            # If both methods fail, return empty results
            logger.warning(f"No results found for query: {query}")
            return []
            
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
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            ) as session:
                async with session.get(self.instant_answer_url, params=params) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            data = await response.json()
                            results = self._parse_instant_answer(data, query)
                            logger.info(f"Instant answer API returned {len(results)} results")
                            return results
                        else:
                            logger.warning(f"Instant answer API returned non-JSON content: {content_type}")
                    else:
                        logger.warning(f"Instant answer API returned status {response.status}")
        except Exception as e:
            logger.warning(f"Instant answer search failed: {e}")
        
        return []
    
    async def _search_html(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo HTML interface"""
        params = {
            'q': query,
            'kl': 'us-en'
        }
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            ) as session:
                async with session.get(self.html_search_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        results = self._parse_html_results(html, max_results)
                        logger.info(f"HTML search returned {len(results)} results")
                        return results
                    else:
                        logger.warning(f"HTML search returned status {response.status}")
        except Exception as e:
            logger.warning(f"HTML search failed: {e}")
        
        return []
    
    def _parse_instant_answer(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse instant answer API response"""
        results = []
        
        # Abstract text (main result)
        if data.get('Abstract'):
            results.append(SearchResult(
                title=data.get('Heading', query),
                snippet=data.get('Abstract', ''),
                url=data.get('AbstractURL', ''),
                source='DuckDuckGo Instant Answer'
            ))
        
        # Definition (if available)
        if data.get('Definition'):
            results.append(SearchResult(
                title=f"Definition: {query}",
                snippet=data.get('Definition', ''),
                url=data.get('DefinitionURL', ''),
                source='DuckDuckGo Definition'
            ))
        
        # Related topics
        for topic in data.get('RelatedTopics', []):
            if isinstance(topic, dict) and topic.get('Text'):
                title = topic.get('FirstURL', '').split('/')[-1] if topic.get('FirstURL') else 'Related Topic'
                # Clean up title
                title = title.replace('_', ' ').replace('-', ' ').title()
                results.append(SearchResult(
                    title=title,
                    snippet=topic.get('Text', ''),
                    url=topic.get('FirstURL', ''),
                    source='DuckDuckGo Related Topics'
                ))
        
        # Answer (if available)
        if data.get('Answer'):
            results.append(SearchResult(
                title=f"Answer: {query}",
                snippet=data.get('Answer', ''),
                url=data.get('AnswerURL', ''),
                source='DuckDuckGo Answer'
            ))
        
        return results
    
    def _parse_html_results(self, html: str, max_results: int) -> List[SearchResult]:
        """Parse HTML search results using multiple regex patterns"""
        results = []
        
        import re
        
        # Multiple patterns to try for DuckDuckGo HTML results
        patterns = [
            # Pattern 1: Standard DuckDuckGo result format
            (r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result__a[^"]*"[^>]*>([^<]+)</a>', 
             r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>([^<]+)</a>'),
            
            # Pattern 2: Alternative DuckDuckGo format
            (r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>',
             r'<span[^>]+class="[^"]*result__snippet[^"]*"[^>]*>([^<]+)</span>'),
            
            # Pattern 3: Generic link pattern
            (r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
             r'<p[^>]*>([^<]+)</p>'),
            
            # Pattern 4: Simple link extraction
            (r'href="([^"]+)"[^>]*>([^<]+)</a>',
             r'<p[^>]*>([^<]+)</p>')
        ]
        
        for link_pattern, snippet_pattern in patterns:
            links = re.findall(link_pattern, html, re.IGNORECASE | re.DOTALL)
            snippets = re.findall(snippet_pattern, html, re.IGNORECASE | re.DOTALL)
            
            if links:
                logger.info(f"Found {len(links)} links with pattern")
                break
        
        if not links:
            logger.warning("No links found with any pattern")
            return results
        
        # Process results
        for i, (url, title) in enumerate(links[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ''
            
            # Clean up the URL
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = 'https://duckduckgo.com' + url
            elif not url.startswith('http'):
                url = 'https://' + url
            
            # Clean up title and snippet
            title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            
            # Skip if title is too short or looks like navigation
            if (len(title) < 3 or 
                title.lower() in ['more', 'next', 'previous', 'search', 'duckduckgo'] or
                'duckduckgo.com' in url.lower()):
                continue
            
            # Skip if URL is not a real website
            if any(skip in url.lower() for skip in ['javascript:', 'mailto:', '#', 'duckduckgo.com']):
                continue
            
            results.append(SearchResult(
                title=title,
                snippet=snippet,
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
