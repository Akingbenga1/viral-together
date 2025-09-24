"""
Data Source Factory for managing different types of data sources
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.interfaces import SocialMediaMetrics, TrendingContent, MarketRate, CompetitorAnalysis

logger = logging.getLogger(__name__)


class BaseDataSource(ABC):
    """Base class for all data sources"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.enabled = True
    
    @abstractmethod
    async def get_user_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        """Get user metrics from this data source"""
        pass
    
    @abstractmethod
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content from this data source"""
        pass
    
    @abstractmethod
    async def get_market_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        """Get market rates from this data source"""
        pass
    
    @abstractmethod
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis from this data source"""
        pass


class MCPDataSource(BaseDataSource):
    """MCP Server data source implementation"""
    
    def __init__(self, mcp_client):
        super().__init__("mcp")
        self.mcp_client = mcp_client
    
    async def get_user_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        """Get user metrics from MCP servers"""
        try:
            if platform == "twitter" and settings.MCP_TWITTER_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "twitter-tools", 
                    "get_tweet_metrics", 
                    {"username": username}
                )
                if "error" not in result:
                    return SocialMediaMetrics(
                        platform=platform,
                        followers=result.get("followers", 0),
                        engagement_rate=result.get("engagement_rate", 0.0),
                        reach=result.get("reach", 0),
                        impressions=result.get("impressions", 0),
                        likes=result.get("likes", 0),
                        comments=result.get("comments", 0),
                        shares=result.get("shares", 0),
                        timestamp=result.get("timestamp")
                    )
            
            elif platform == "youtube" and settings.MCP_YOUTUBE_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "youtube-tools",
                    "get_video_stats",
                    {"channel_id": username}
                )
                if "error" not in result:
                    return SocialMediaMetrics(
                        platform=platform,
                        followers=result.get("subscribers", 0),
                        engagement_rate=result.get("engagement_rate", 0.0),
                        reach=result.get("views", 0),
                        impressions=result.get("views", 0),
                        likes=result.get("likes", 0),
                        comments=result.get("comments", 0),
                        shares=result.get("shares", 0),
                        timestamp=result.get("timestamp")
                    )
            
            elif platform == "tiktok" and settings.MCP_TIKTOK_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "tiktok-tools",
                    "get_video_analytics",
                    {"username": username}
                )
                if "error" not in result:
                    return SocialMediaMetrics(
                        platform=platform,
                        followers=result.get("followers", 0),
                        engagement_rate=result.get("engagement_rate", 0.0),
                        reach=result.get("views", 0),
                        impressions=result.get("views", 0),
                        likes=result.get("likes", 0),
                        comments=result.get("comments", 0),
                        shares=result.get("shares", 0),
                        timestamp=result.get("timestamp")
                    )
            
            elif platform == "instagram" and settings.MCP_INSTAGRAM_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "instagram-tools",
                    "get_media_insights",
                    {"username": username}
                )
                if "error" not in result:
                    return SocialMediaMetrics(
                        platform=platform,
                        followers=result.get("followers", 0),
                        engagement_rate=result.get("engagement_rate", 0.0),
                        reach=result.get("reach", 0),
                        impressions=result.get("impressions", 0),
                        likes=result.get("likes", 0),
                        comments=result.get("comments", 0),
                        shares=result.get("saves", 0),
                        timestamp=result.get("timestamp")
                    )
            
        except Exception as e:
            logger.error(f"MCP DataSource: Error getting user metrics for {username} on {platform}: {e}")
        
        return None
    
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content from MCP servers"""
        try:
            trending_content = []
            
            if platform == "twitter" and settings.MCP_TWITTER_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "twitter-tools",
                    "search_tweets",
                    {"query": f"#{category or 'trending'}"}
                )
                if "error" not in result and "trends" in result:
                    for trend in result["trends"]:
                        trending_content.append(TrendingContent(
                            platform=platform,
                            hashtag=trend,
                            post_count=0,
                            engagement_rate=0.0,
                            trend_score=0.0,
                            category=category or "general",
                            timestamp=result.get("timestamp")
                        ))
            
            elif platform == "tiktok" and settings.MCP_TIKTOK_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "tiktok-tools",
                    "get_trending_hashtags",
                    {}
                )
                if "error" not in result and "trending_hashtags" in result:
                    for hashtag in result["trending_hashtags"]:
                        trending_content.append(TrendingContent(
                            platform=platform,
                            hashtag=hashtag,
                            post_count=0,
                            engagement_rate=0.0,
                            trend_score=0.0,
                            category=category or "general",
                            timestamp=result.get("timestamp")
                        ))
            
            elif platform == "youtube" and settings.MCP_YOUTUBE_ENABLED:
                result = await self.mcp_client.call_mcp_server(
                    "youtube-tools",
                    "get_trending_hashtags",
                    {}
                )
                if "error" not in result and "trending_hashtags" in result:
                    for hashtag in result["trending_hashtags"]:
                        trending_content.append(TrendingContent(
                            platform=platform,
                            hashtag=hashtag,
                            post_count=0,
                            engagement_rate=0.0,
                            trend_score=0.0,
                            category=category or "general",
                            timestamp=result.get("timestamp")
                        ))
            
            return trending_content
            
        except Exception as e:
            logger.error(f"MCP DataSource: Error getting trending content for {platform}: {e}")
            return []
    
    async def get_market_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        """Get market rates from MCP servers (limited capability)"""
        # MCP servers typically don't provide market rate data
        # This would need to be supplemented by other sources
        return []
    
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis from MCP servers (limited capability)"""
        # MCP servers typically don't provide competitor analysis
        # This would need to be supplemented by other sources
        return []


class DirectAPIDataSource(BaseDataSource):
    """Direct API data source implementation"""
    
    def __init__(self, social_media_factory):
        super().__init__("direct_api")
        self.social_media_factory = social_media_factory
    
    async def get_user_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        """Get user metrics from direct APIs"""
        try:
            if platform == "twitter" and settings.DIRECT_API_TWITTER_ENABLED:
                social_service = self.social_media_factory.create_social_media_service("twitter")
                async with social_service:
                    return await social_service.get_user_metrics(username)
            
            elif platform == "youtube" and settings.DIRECT_API_YOUTUBE_ENABLED:
                social_service = self.social_media_factory.create_social_media_service("youtube")
                async with social_service:
                    return await social_service.get_user_metrics(username)
            
            elif platform == "tiktok" and settings.DIRECT_API_TIKTOK_ENABLED:
                social_service = self.social_media_factory.create_social_media_service("tiktok")
                async with social_service:
                    return await social_service.get_user_metrics(username)
            
            elif platform == "instagram" and settings.DIRECT_API_INSTAGRAM_ENABLED:
                social_service = self.social_media_factory.create_social_media_service("instagram")
                async with social_service:
                    return await social_service.get_user_metrics(username)
            
        except Exception as e:
            logger.error(f"Direct API DataSource: Error getting user metrics for {username} on {platform}: {e}")
        
        return None
    
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content from direct APIs"""
        try:
            if platform in ["twitter", "youtube", "tiktok", "instagram"]:
                social_service = self.social_media_factory.create_social_media_service(platform)
                async with social_service:
                    return await social_service.get_trending_hashtags(platform, limit=20)
            
        except Exception as e:
            logger.error(f"Direct API DataSource: Error getting trending content for {platform}: {e}")
        
        return []
    
    async def get_market_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        """Get market rates from direct APIs (limited capability)"""
        # Direct APIs typically don't provide market rate data
        # This would need to be supplemented by other sources
        return []
    
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis from direct APIs (limited capability)"""
        # Direct APIs typically don't provide competitor analysis
        # This would need to be supplemented by other sources
        return []


class ThirdPartyDataSource(BaseDataSource):
    """3rd Party Analytics API data source implementation"""
    
    def __init__(self):
        super().__init__("third_party")
    
    async def get_user_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        """Get user metrics from 3rd party APIs"""
        try:
            # Social Blade API
            if settings.THIRD_PARTY_SOCIALBLADE_ENABLED and settings.SOCIALBLADE_API_KEY:
                metrics = await self._get_socialblade_metrics(username, platform)
                if metrics:
                    return metrics
            
            # Hootsuite API
            if settings.THIRD_PARTY_HOOTSUITE_ENABLED and settings.HOOTSUITE_API_KEY:
                metrics = await self._get_hootsuite_metrics(username, platform)
                if metrics:
                    return metrics
            
            # Sprout Social API
            if settings.THIRD_PARTY_SPROUT_ENABLED and settings.SPROUT_SOCIAL_API_KEY:
                metrics = await self._get_sprout_metrics(username, platform)
                if metrics:
                    return metrics
            
        except Exception as e:
            logger.error(f"3rd Party DataSource: Error getting user metrics for {username} on {platform}: {e}")
        
        return None
    
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content from 3rd party APIs"""
        try:
            trending_content = []
            
            # Brandwatch API for trending topics
            if settings.THIRD_PARTY_BRANDWATCH_ENABLED and settings.BRANDWATCH_API_KEY:
                content = await self._get_brandwatch_trends(platform, category)
                trending_content.extend(content)
            
            # Buffer API for trending content
            if settings.THIRD_PARTY_BUFFER_ENABLED and settings.BUFFER_API_KEY:
                content = await self._get_buffer_trends(platform, category)
                trending_content.extend(content)
            
            return trending_content
            
        except Exception as e:
            logger.error(f"3rd Party DataSource: Error getting trending content for {platform}: {e}")
            return []
    
    async def get_market_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        """Get market rates from 3rd party APIs"""
        try:
            market_rates = []
            
            # Social Blade for market rates
            if settings.THIRD_PARTY_SOCIALBLADE_ENABLED and settings.SOCIALBLADE_API_KEY:
                rates = await self._get_socialblade_rates(platform, content_type)
                market_rates.extend(rates)
            
            # Hootsuite for market analysis
            if settings.THIRD_PARTY_HOOTSUITE_ENABLED and settings.HOOTSUITE_API_KEY:
                rates = await self._get_hootsuite_rates(platform, content_type)
                market_rates.extend(rates)
            
            return market_rates
            
        except Exception as e:
            logger.error(f"3rd Party DataSource: Error getting market rates for {platform}: {e}")
            return []
    
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis from 3rd party APIs"""
        try:
            competitor_analyses = []
            
            # Brandwatch for competitor analysis
            if settings.THIRD_PARTY_BRANDWATCH_ENABLED and settings.BRANDWATCH_API_KEY:
                analysis = await self._get_brandwatch_competitors(competitors)
                competitor_analyses.extend(analysis)
            
            # Sprout Social for competitor insights
            if settings.THIRD_PARTY_SPROUT_ENABLED and settings.SPROUT_SOCIAL_API_KEY:
                analysis = await self._get_sprout_competitors(competitors)
                competitor_analyses.extend(analysis)
            
            return competitor_analyses
            
        except Exception as e:
            logger.error(f"3rd Party DataSource: Error getting competitor analysis: {e}")
            return []
    
    # Helper methods for 3rd party API calls (implementations would go here)
    async def _get_socialblade_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        # Implementation for Social Blade API
        return None
    
    async def _get_hootsuite_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        # Implementation for Hootsuite API
        return None
    
    async def _get_sprout_metrics(self, username: str, platform: str) -> Optional[SocialMediaMetrics]:
        # Implementation for Sprout Social API
        return None
    
    async def _get_brandwatch_trends(self, platform: str, category: str = None) -> List[TrendingContent]:
        # Implementation for Brandwatch API
        return []
    
    async def _get_buffer_trends(self, platform: str, category: str = None) -> List[TrendingContent]:
        # Implementation for Buffer API
        return []
    
    async def _get_socialblade_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        # Implementation for Social Blade market rates
        return []
    
    async def _get_hootsuite_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        # Implementation for Hootsuite market rates
        return []
    
    async def _get_brandwatch_competitors(self, competitors: List[str]) -> List[CompetitorAnalysis]:
        # Implementation for Brandwatch competitor analysis
        return []
    
    async def _get_sprout_competitors(self, competitors: List[str]) -> List[CompetitorAnalysis]:
        # Implementation for Sprout Social competitor analysis
        return []


class DataSourceFactory:
    """Factory for creating and managing data sources"""
    
    def __init__(self, mcp_client=None, social_media_factory=None):
        self.mcp_client = mcp_client
        self.social_media_factory = social_media_factory
    
    def create_mcp_sources(self) -> List[MCPDataSource]:
        """Create MCP data sources if enabled"""
        sources = []
        if settings.MCP_ENABLED and self.mcp_client:
            sources.append(MCPDataSource(self.mcp_client))
        return sources
    
    def create_direct_api_sources(self) -> List[DirectAPIDataSource]:
        """Create direct API data sources if enabled"""
        sources = []
        if settings.DIRECT_API_ENABLED and self.social_media_factory:
            sources.append(DirectAPIDataSource(self.social_media_factory))
        return sources
    
    def create_third_party_sources(self) -> List[ThirdPartyDataSource]:
        """Create 3rd party data sources if enabled"""
        sources = []
        if settings.THIRD_PARTY_ENABLED:
            sources.append(ThirdPartyDataSource())
        return sources
    
    def get_all_sources(self) -> List[BaseDataSource]:
        """Get all enabled data sources"""
        sources = []
        sources.extend(self.create_mcp_sources())
        sources.extend(self.create_direct_api_sources())
        sources.extend(self.create_third_party_sources())
        return sources
    
    def get_available_sources(self) -> List[str]:
        """Get list of available source types"""
        sources = []
        if settings.MCP_ENABLED:
            sources.append("mcp")
        if settings.DIRECT_API_ENABLED:
            sources.append("direct_api")
        if settings.THIRD_PARTY_ENABLED:
            sources.append("third_party")
        return sources
    
    def get_platform_sources(self, platform: str) -> List[str]:
        """Get available sources for a specific platform"""
        sources = []
        
        if settings.MCP_ENABLED:
            platform_attr = f"MCP_{platform.upper()}_ENABLED"
            if hasattr(settings, platform_attr) and getattr(settings, platform_attr):
                sources.append("mcp")
        
        if settings.DIRECT_API_ENABLED:
            platform_attr = f"DIRECT_API_{platform.upper()}_ENABLED"
            if hasattr(settings, platform_attr) and getattr(settings, platform_attr):
                sources.append("direct_api")
        
        if settings.THIRD_PARTY_ENABLED:
            sources.append("third_party")
        
        return sources
