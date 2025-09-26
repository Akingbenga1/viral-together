"""
Real-time analytics service implementation with multi-source data architecture
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.interfaces import IAnalyticsService, SocialMediaMetrics, MarketRate, CompetitorAnalysis, TrendingContent
from app.services.social_media.social_media_factory import SocialMediaFactory
from app.services.web_search.web_search_factory import WebSearchFactory
from app.services.mcp_client import MCPClient
from app.services.analytics.data_source_factory import DataSourceFactory, BaseDataSource
from app.core.config import settings

logger = logging.getLogger(__name__)


class RealTimeAnalyticsService(IAnalyticsService):
    """Real-time analytics service implementation with multi-source data architecture"""
    
    def __init__(self):
        self.social_media_factory = SocialMediaFactory()
        self.web_search_factory = WebSearchFactory()
        self.mcp_client = MCPClient()
        self.data_source_factory = DataSourceFactory(
            mcp_client=self.mcp_client,
            social_media_factory=self.social_media_factory
        )
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = settings.REAL_TIME_DATA_CACHE_TTL
    
    async def get_engagement_trends(self, user_id: int, days: int = 30) -> List[SocialMediaMetrics]:
        """Get engagement trends for a user using multi-source data architecture"""
        try:
            cache_key = f"engagement_trends_{user_id}_{days}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Get user's social media accounts (this would come from database)
            user_accounts = await self._get_user_social_accounts(user_id)
            
            all_metrics = []
            for account in user_accounts:
                platform = account['platform']
                username = account['username']
                
                # Get metrics from all enabled data sources
                metrics_data = await self._get_metrics_from_all_sources(username, platform)
                
                # Add all metrics from different sources
                for source_name, metrics in metrics_data.items():
                    if metrics:
                        all_metrics.append(metrics)
            
            # Cache the results
            self.cache[cache_key] = {
                'data': all_metrics,
                'timestamp': datetime.now()
            }
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Failed to get engagement trends: {e}")
            return []
    
    async def get_market_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        """Get current market rates for content using multi-source data architecture"""
        try:
            cache_key = f"market_rates_{platform}_{content_type}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Get market rates from all enabled data sources
            rates_data = await self._get_market_rates_from_all_sources(platform, content_type)
            
            # Combine all market rates from different sources
            all_market_rates = []
            for source_name, rates_list in rates_data.items():
                all_market_rates.extend(rates_list)
            
            # If no rates from data sources, fall back to web search
            if not all_market_rates:
                search_service = self.web_search_factory.create_search_service()
                
                async with search_service:
                    # Search for current market rates
                    query = f"{platform} influencer rates {content_type} 2024"
                    search_results = await search_service.search(query, max_results=10)
                    
                    # Parse market rates from search results
                    all_market_rates = self._parse_market_rates_from_search(search_results, platform, content_type)
            
            # Cache the results
            self.cache[cache_key] = {
                'data': all_market_rates,
                'timestamp': datetime.now()
            }
            
            return all_market_rates
            
        except Exception as e:
            logger.error(f"Failed to get market rates: {e}")
            return []
    
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis using multi-source data architecture"""
        try:
            cache_key = f"competitor_analysis_{user_id}_{hash(tuple(competitors))}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Get competitor analysis from all enabled data sources
            analysis_data = await self._get_competitor_analysis_from_all_sources(user_id, competitors)
            
            # Combine all competitor analysis from different sources
            all_competitor_analyses = []
            for source_name, analysis_list in analysis_data.items():
                all_competitor_analyses.extend(analysis_list)
            
            # Cache the results
            self.cache[cache_key] = {
                'data': all_competitor_analyses,
                'timestamp': datetime.now()
            }
            
            return all_competitor_analyses
            
        except Exception as e:
            logger.error(f"Failed to get competitor analysis: {e}")
            return []
    
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content for a platform using multi-source data architecture"""
        logger.info(f"Starting to get trending content for platform: {platform}, category: {category or 'all'}")
        try:
            cache_key = f"trending_content_{platform}_{category or 'all'}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                cached_data = self.cache[cache_key]['data']
                logger.info(f"Cache hit for {platform} trending content: {len(cached_data)} items found")
                return cached_data
            else:
                logger.info(f"Cache miss for {platform} trending content, fetching fresh data")
            
            # Get trending content from all enabled data sources
            trending_data = await self._get_trending_from_all_sources(platform, category)
            
            # Combine all trending content from different sources
            all_trending_content = []
            total_items = 0
            for source_name, trending_list in trending_data.items():
                all_trending_content.extend(trending_list)
                total_items += len(trending_list)
                logger.info(f"Data source {source_name} returned {len(trending_list)} trending items for {platform}")
            
            logger.info(f"Combined {total_items} trending items from {len(trending_data)} data sources for {platform}")
            
            # Cache the results
            self.cache[cache_key] = {
                'data': all_trending_content,
                'timestamp': datetime.now()
            }
            
            return all_trending_content
            
        except Exception as e:
            logger.error(f"Failed to get trending content: {e}")
            return []
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_entry = self.cache[cache_key]
        age = (datetime.now() - cache_entry['timestamp']).seconds
        
        return age < self.cache_ttl
    
    async def _get_metrics_from_all_sources(self, username: str, platform: str) -> Dict[str, Optional[SocialMediaMetrics]]:
        """Get metrics from all enabled data sources"""
        metrics_data = {}
        
        # Get all enabled data sources
        data_sources = self.data_source_factory.get_all_sources()
        
        for source in data_sources:
            try:
                metrics = await source.get_user_metrics(username, platform)
                metrics_data[source.source_name] = metrics
            except Exception as e:
                logger.warning(f"Failed to get metrics from {source.source_name} for {username} on {platform}: {e}")
                metrics_data[source.source_name] = None
        
        return metrics_data
    
    async def _get_trending_from_all_sources(self, platform: str, category: str = None) -> Dict[str, List[TrendingContent]]:
        """Get trending content from all enabled data sources"""
        trending_data = {}
        
        # Get all enabled data sources
        data_sources = self.data_source_factory.get_all_sources()
        logger.info(f"Using {len(data_sources)} data sources for {platform}: {[s.source_name for s in data_sources]}")
        
        for source in data_sources:
            try:
                trending = await source.get_trending_content(platform, category)
                trending_data[source.source_name] = trending
            except Exception as e:
                logger.warning(f"Failed to get trending content from {source.source_name} for {platform}: {e}")
                trending_data[source.source_name] = []
        
        return trending_data
    
    async def _get_market_rates_from_all_sources(self, platform: str, content_type: str) -> Dict[str, List[MarketRate]]:
        """Get market rates from all enabled data sources"""
        rates_data = {}
        
        # Get all enabled data sources
        data_sources = self.data_source_factory.get_all_sources()
        
        for source in data_sources:
            try:
                rates = await source.get_market_rates(platform, content_type)
                rates_data[source.source_name] = rates
            except Exception as e:
                logger.warning(f"Failed to get market rates from {source.source_name} for {platform}: {e}")
                rates_data[source.source_name] = []
        
        return rates_data
    
    async def _get_competitor_analysis_from_all_sources(self, user_id: int, competitors: List[str]) -> Dict[str, List[CompetitorAnalysis]]:
        """Get competitor analysis from all enabled data sources"""
        analysis_data = {}
        
        # Get all enabled data sources
        data_sources = self.data_source_factory.get_all_sources()
        
        for source in data_sources:
            try:
                analysis = await source.get_competitor_analysis(user_id, competitors)
                analysis_data[source.source_name] = analysis
            except Exception as e:
                logger.warning(f"Failed to get competitor analysis from {source.source_name}: {e}")
                analysis_data[source.source_name] = []
        
        return analysis_data

    async def _get_user_social_accounts(self, user_id: int) -> List[Dict[str, str]]:
        """Get user's social media accounts from database"""
        # This would typically query the database
        # For now, return mock data
        return [
            {'platform': 'twitter', 'username': 'example_user'},
            {'platform': 'instagram', 'username': 'example_user'},
            {'platform': 'youtube', 'username': 'example_user'}
        ]
    
    # TEMPORARILY DISABLED: _get_competitor_accounts function
    # async def _get_competitor_accounts(self, competitor: str) -> List[Dict[str, str]]:
    #     """Get competitor's social media accounts"""
    #     # This would typically query the database or use search
    #     # For now, return mock data
    #     return [
    #         {'platform': 'twitter', 'username': competitor},
    #         {'platform': 'instagram', 'username': competitor}
    #     ]
    
    def _parse_market_rates_from_search(self, search_results: List, platform: str, content_type: str) -> List[MarketRate]:
        """Parse market rates from search results"""
        market_rates = []
        
        # This is a simplified parser
        # In a real implementation, you'd use NLP to extract rate information
        for result in search_results:
            # Look for rate information in the snippet
            snippet = result.snippet.lower()
            
            # Simple rate extraction (this would be more sophisticated in reality)
            if '$' in snippet and any(word in snippet for word in ['rate', 'price', 'cost']):
                # Extract rate ranges (simplified)
                import re
                rate_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', snippet)
                
                if rate_matches:
                    rates = [float(rate.replace(',', '')) for rate in rate_matches]
                    min_rate = min(rates)
                    max_rate = max(rates)
                    
                    market_rate = MarketRate(
                        platform=platform,
                        content_type=content_type,
                        follower_range="varies",
                        rate_range={"min": min_rate, "max": max_rate, "currency": "USD"},
                        engagement_threshold=0.0,
                        timestamp=datetime.now()
                    )
                    
                    market_rates.append(market_rate)
        
        return market_rates
