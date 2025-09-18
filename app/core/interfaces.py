"""
Core interfaces for the AI agent system following SOLID principles.
These interfaces ensure interchangeability and proper separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Standardized search result structure"""
    title: str
    snippet: str
    url: str
    published_date: Optional[datetime] = None
    relevance_score: Optional[float] = None
    source: Optional[str] = None


@dataclass
class SocialMediaMetrics:
    """Standardized social media metrics structure"""
    platform: str
    followers: int
    engagement_rate: float
    reach: int
    impressions: int
    likes: int
    comments: int
    shares: int
    timestamp: datetime


@dataclass
class TrendingContent:
    """Standardized trending content structure"""
    platform: str
    hashtag: str
    post_count: int
    engagement_rate: float
    trend_score: float
    category: str
    timestamp: datetime


@dataclass
class MarketRate:
    """Standardized market rate structure"""
    platform: str
    content_type: str
    follower_range: str
    rate_range: Dict[str, float]  # {"min": 100, "max": 500, "currency": "USD"}
    engagement_threshold: float
    timestamp: datetime


@dataclass
class CompetitorAnalysis:
    """Standardized competitor analysis structure"""
    competitor_name: str
    platform: str
    followers: int
    engagement_rate: float
    content_frequency: float
    top_performing_content: List[str]
    growth_rate: float
    timestamp: datetime


class IWebSearchService(ABC):
    """Interface for web search services"""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search the web for relevant information"""
        pass
    
    @abstractmethod
    async def search_trends(self, topic: str, timeframe: str = "7d") -> List[SearchResult]:
        """Search for trending information about a topic"""
        pass
    
    @abstractmethod
    async def search_news(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search for recent news about a topic"""
        pass


class ISocialMediaAPIService(ABC):
    """Interface for social media API services"""
    
    @abstractmethod
    async def get_user_metrics(self, username: str) -> SocialMediaMetrics:
        """Get user metrics from social media platform"""
        pass
    
    @abstractmethod
    async def get_trending_hashtags(self, platform: str, limit: int = 20) -> List[TrendingContent]:
        """Get trending hashtags for a platform"""
        pass
    
    @abstractmethod
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a specific post"""
        pass
    
    @abstractmethod
    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for posts on the platform"""
        pass


class IAnalyticsService(ABC):
    """Interface for analytics services"""
    
    @abstractmethod
    async def get_engagement_trends(self, user_id: int, days: int = 30) -> List[SocialMediaMetrics]:
        """Get engagement trends for a user"""
        pass
    
    @abstractmethod
    async def get_market_rates(self, platform: str, content_type: str) -> List[MarketRate]:
        """Get current market rates for content"""
        pass
    
    @abstractmethod
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis"""
        pass
    
    @abstractmethod
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content for a platform"""
        pass


class IInfluencerMarketingService(ABC):
    """Interface for influencer marketing services"""
    
    @abstractmethod
    async def get_brand_partnership_opportunities(self, user_id: int) -> List[Dict[str, Any]]:
        """Get brand partnership opportunities"""
        pass
    
    @abstractmethod
    async def get_content_recommendations(self, user_id: int, platform: str) -> List[Dict[str, Any]]:
        """Get content recommendations based on trends"""
        pass
    
    @abstractmethod
    async def get_pricing_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Get pricing recommendations based on market analysis"""
        pass
    
    @abstractmethod
    async def get_growth_strategies(self, user_id: int) -> List[Dict[str, Any]]:
        """Get growth strategies based on current trends"""
        pass


class IRealTimeDataService(ABC):
    """Interface for real-time data services"""
    
    @abstractmethod
    async def get_live_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get live metrics for a user"""
        pass
    
    @abstractmethod
    async def get_trending_topics(self, platform: str) -> List[str]:
        """Get trending topics for a platform"""
        pass
    
    @abstractmethod
    async def get_market_insights(self, industry: str) -> Dict[str, Any]:
        """Get market insights for an industry"""
        pass


class IAIAgentService(ABC):
    """Interface for AI agent services"""
    
    @abstractmethod
    async def execute_with_real_time_data(
        self, 
        agent_id: int, 
        prompt: str, 
        context: Dict[str, Any],
        real_time_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent task with real-time data"""
        pass
    
    @abstractmethod
    async def get_enhanced_recommendations(
        self, 
        user_id: int, 
        agent_type: str,
        real_time_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get enhanced recommendations with real-time data"""
        pass


class IDataProvider(ABC):
    """Interface for data providers (APIs, databases, etc.)"""
    
    @abstractmethod
    async def fetch_data(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from a data source"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the data provider is available"""
        pass
    
    @abstractmethod
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information"""
        pass
