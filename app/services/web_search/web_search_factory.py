"""
Web search service factory for creating different search providers
"""

from typing import Optional
from app.core.interfaces import IWebSearchService
from app.services.web_search.duckduckgo_search import DuckDuckGoSearchService
from app.services.web_search.google_search import GoogleSearchService
from app.services.web_search.mcp_web_search_service import MCPWebSearchService
from app.services.mcp_client import MCPClient
from app.core.config import settings


class WebSearchFactory:
    """Factory for creating web search services"""
    
    @staticmethod
    def create_search_service(provider: str = "mcp", **kwargs) -> IWebSearchService:
        """
        Create a web search service based on the provider
        
        Args:
            provider: Search provider ("mcp", "duckduckgo", "google")
            **kwargs: Additional configuration parameters
        
        Returns:
            IWebSearchService: Configured search service
        """
        provider = provider.lower()
        
        if provider == "mcp":
            mcp_client = kwargs.get('mcp_client') or MCPClient()
            return MCPWebSearchService(mcp_client)
        
        elif provider == "duckduckgo":
            return DuckDuckGoSearchService()
        
        elif provider == "google":
            api_key = kwargs.get('api_key') or settings.WEB_SEARCH_API_KEY
            search_engine_id = kwargs.get('search_engine_id') or settings.WEB_SEARCH_ENGINE_ID
            
            if not api_key or not search_engine_id:
                raise ValueError("Google search requires API key and search engine ID")
            
            return GoogleSearchService(api_key=api_key, search_engine_id=search_engine_id)
        
        else:
            raise ValueError(f"Unsupported search provider: {provider}")
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available search providers"""
        return ["mcp", "duckduckgo", "google"]
    
    @staticmethod
    def get_default_provider() -> str:
        """Get the default search provider"""
        return "mcp"  # Use MCP for enhanced architecture
