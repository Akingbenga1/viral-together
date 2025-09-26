"""
MCP Web Search Service - Uses MCP servers for web search instead of direct API calls
"""

import logging
from typing import List, Dict, Any, Optional
from app.core.interfaces import IWebSearchService
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class MCPWebSearchService(IWebSearchService):
    """MCP-based web search service"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.is_initialized = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the search service"""
        try:
            logger.info("MCPWebSearchService: Initializing MCP web search service")
            self.is_initialized = True
            logger.info("MCPWebSearchService: Successfully initialized")
        except Exception as e:
            logger.error(f"MCPWebSearchService: Failed to initialize: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup the search service"""
        try:
            logger.info("MCPWebSearchService: Cleaning up MCP web search service")
            self.is_initialized = False
            logger.info("MCPWebSearchService: Successfully cleaned up")
        except Exception as e:
            logger.error(f"MCPWebSearchService: Failed to cleanup: {e}")
    
    async def search_trends(self, query: str, timeframe: str = "7d", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for trending topics using MCP"""
        try:
            logger.info(f"MCPWebSearchService: Searching trends for query '{query}' with timeframe '{timeframe}' (limit: {limit})")
            
            if not self.is_initialized:
                await self.initialize()
            
            # Use MCP to search for trends
            search_results = await self.mcp_client.call_mcp_server(
                server_name="web-search-tools",  # Assuming we have a web search MCP server
                tool_name="search_trends",
                parameters={
                    "query": query,
                    "timeframe": timeframe,
                    "limit": limit
                }
            )
            
            if "error" in search_results:
                logger.warning(f"MCPWebSearchService: MCP search failed: {search_results['error']}")
                return []
            
            # Format results
            formatted_results = []
            for result in search_results.get("results", []):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "url": result.get("url", ""),
                    "relevance_score": result.get("relevance_score", 0.0),
                    "timestamp": result.get("timestamp", "")
                })
            
            logger.info(f"MCPWebSearchService: Found {len(formatted_results)} trend results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"MCPWebSearchService: Failed to search trends: {e}")
            return []
    
    async def search_influencers(self, query: str, platform: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for influencers using MCP"""
        try:
            logger.info(f"MCPWebSearchService: Searching influencers for query '{query}' on platform '{platform}' (limit: {limit})")
            
            if not self.is_initialized:
                await self.initialize()
            
            # Use MCP to search for influencers
            search_results = await self.mcp_client.call_mcp_server(
                server_name="web-search-tools",
                tool_name="search_influencers",
                parameters={
                    "query": query,
                    "platform": platform,
                    "limit": limit
                }
            )
            
            if "error" in search_results:
                logger.warning(f"MCPWebSearchService: MCP influencer search failed: {search_results['error']}")
                return []
            
            # Format results
            formatted_results = []
            for result in search_results.get("influencers", []):
                formatted_results.append({
                    "name": result.get("name", ""),
                    "username": result.get("username", ""),
                    "platform": result.get("platform", ""),
                    "followers": result.get("followers", 0),
                    "engagement_rate": result.get("engagement_rate", 0.0),
                    "bio": result.get("bio", ""),
                    "profile_url": result.get("profile_url", "")
                })
            
            logger.info(f"MCPWebSearchService: Found {len(formatted_results)} influencer results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"MCPWebSearchService: Failed to search influencers: {e}")
            return []
    
    async def search_content(self, query: str, platform: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for content using MCP"""
        try:
            logger.info(f"MCPWebSearchService: Searching content for query '{query}' on platform '{platform}' (limit: {limit})")
            
            if not self.is_initialized:
                await self.initialize()
            
            # Use MCP to search for content
            search_results = await self.mcp_client.call_mcp_server(
                server_name="web-search-tools",
                tool_name="search_content",
                parameters={
                    "query": query,
                    "platform": platform,
                    "limit": limit
                }
            )
            
            if "error" in search_results:
                logger.warning(f"MCPWebSearchService: MCP content search failed: {search_results['error']}")
                return []
            
            # Format results
            formatted_results = []
            for result in search_results.get("content", []):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "description": result.get("description", ""),
                    "platform": result.get("platform", ""),
                    "author": result.get("author", ""),
                    "engagement": result.get("engagement", {}),
                    "url": result.get("url", ""),
                    "timestamp": result.get("timestamp", "")
                })
            
            logger.info(f"MCPWebSearchService: Found {len(formatted_results)} content results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"MCPWebSearchService: Failed to search content: {e}")
            return []
    
    async def search_hashtags(self, query: str, platform: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for hashtags using MCP"""
        try:
            logger.info(f"MCPWebSearchService: Searching hashtags for query '{query}' on platform '{platform}' (limit: {limit})")
            
            if not self.is_initialized:
                await self.initialize()
            
            # Use MCP to search for hashtags
            search_results = await self.mcp_client.call_mcp_server(
                server_name="web-search-tools",
                tool_name="search_hashtags",
                parameters={
                    "query": query,
                    "platform": platform,
                    "limit": limit
                }
            )
            
            if "error" in search_results:
                logger.warning(f"MCPWebSearchService: MCP hashtag search failed: {search_results['error']}")
                return []
            
            # Format results
            formatted_results = []
            for result in search_results.get("hashtags", []):
                formatted_results.append({
                    "hashtag": result.get("hashtag", ""),
                    "platform": result.get("platform", ""),
                    "post_count": result.get("post_count", 0),
                    "engagement_rate": result.get("engagement_rate", 0.0),
                    "trend_score": result.get("trend_score", 0.0)
                })
            
            logger.info(f"MCPWebSearchService: Found {len(formatted_results)} hashtag results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"MCPWebSearchService: Failed to search hashtags: {e}")
            return []
