"""
Real-time analytics service implementation
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.interfaces import IAnalyticsService, SocialMediaMetrics, MarketRate, CompetitorAnalysis, TrendingContent
from app.services.social_media.social_media_factory import SocialMediaFactory
from app.services.web_search.web_search_factory import WebSearchFactory

logger = logging.getLogger(__name__)


class RealTimeAnalyticsService(IAnalyticsService):
    """Real-time analytics service implementation"""
    
    def __init__(self):
        self.social_media_factory = SocialMediaFactory()
        self.web_search_factory = WebSearchFactory()
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
    
    async def get_engagement_trends(self, user_id: int, days: int = 30) -> List[SocialMediaMetrics]:
        """Get engagement trends for a user"""
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
                
                try:
                    # Create social media service
                    social_service = self.social_media_factory.create_social_media_service(platform)
                    
                    async with social_service:
                        # Get current metrics
                        metrics = await social_service.get_user_metrics(username)
                        all_metrics.append(metrics)
                        
                except Exception as e:
                    logger.warning(f"Failed to get metrics for {platform}/{username}: {e}")
                    continue
            
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
        """Get current market rates for content"""
        try:
            cache_key = f"market_rates_{platform}_{content_type}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Search for market rate information
            search_service = self.web_search_factory.create_search_service()
            
            async with search_service:
                # Search for current market rates
                query = f"{platform} influencer rates {content_type} 2024"
                search_results = await search_service.search(query, max_results=10)
                
                # Parse market rates from search results
                market_rates = self._parse_market_rates_from_search(search_results, platform, content_type)
            
            # Cache the results
            self.cache[cache_key] = {
                'data': market_rates,
                'timestamp': datetime.now()
            }
            
            return market_rates
            
        except Exception as e:
            logger.error(f"Failed to get market rates: {e}")
            return []
    
    async def get_competitor_analysis(self, user_id: int, competitors: List[str]) -> List[CompetitorAnalysis]:
        """Get competitor analysis"""
        try:
            cache_key = f"competitor_analysis_{user_id}_{hash(tuple(competitors))}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            competitor_analyses = []
            
            for competitor in competitors:
                try:
                    # Get competitor's social media accounts
                    competitor_accounts = await self._get_competitor_accounts(competitor)
                    
                    for account in competitor_accounts:
                        platform = account['platform']
                        username = account['username']
                        
                        try:
                            # Create social media service
                            social_service = self.social_media_factory.create_social_media_service(platform)
                            
                            async with social_service:
                                # Get competitor metrics
                                metrics = await social_service.get_user_metrics(username)
                                
                                # Get recent posts for analysis
                                posts = await social_service.search_posts(f"from:{username}", limit=10)
                                
                                # Analyze top performing content
                                top_posts = sorted(posts, key=lambda x: x.get('engagement_rate', 0), reverse=True)[:3]
                                top_content = [post.get('text', '')[:100] for post in top_posts]
                                
                                analysis = CompetitorAnalysis(
                                    competitor_name=competitor,
                                    platform=platform,
                                    followers=metrics.followers,
                                    engagement_rate=metrics.engagement_rate,
                                    content_frequency=len(posts) / 30,  # Posts per day estimate
                                    top_performing_content=top_content,
                                    growth_rate=0.0,  # Would need historical data
                                    timestamp=datetime.now()
                                )
                                
                                competitor_analyses.append(analysis)
                                
                        except Exception as e:
                            logger.warning(f"Failed to analyze competitor {competitor} on {platform}: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Failed to get competitor accounts for {competitor}: {e}")
                    continue
            
            # Cache the results
            self.cache[cache_key] = {
                'data': competitor_analyses,
                'timestamp': datetime.now()
            }
            
            return competitor_analyses
            
        except Exception as e:
            logger.error(f"Failed to get competitor analysis: {e}")
            return []
    
    async def get_trending_content(self, platform: str, category: str = None) -> List[TrendingContent]:
        """Get trending content for a platform"""
        try:
            cache_key = f"trending_content_{platform}_{category or 'all'}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Create social media service
            social_service = self.social_media_factory.create_social_media_service(platform)
            
            async with social_service:
                # Get trending hashtags
                trending_content = await social_service.get_trending_hashtags(platform, limit=20)
                
                # Filter by category if specified
                if category:
                    trending_content = [tc for tc in trending_content if tc.category == category]
            
            # Cache the results
            self.cache[cache_key] = {
                'data': trending_content,
                'timestamp': datetime.now()
            }
            
            return trending_content
            
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
    
    async def _get_user_social_accounts(self, user_id: int) -> List[Dict[str, str]]:
        """Get user's social media accounts from database"""
        # This would typically query the database
        # For now, return mock data
        return [
            {'platform': 'twitter', 'username': 'example_user'},
            {'platform': 'instagram', 'username': 'example_user'},
            {'platform': 'youtube', 'username': 'example_user'}
        ]
    
    async def _get_competitor_accounts(self, competitor: str) -> List[Dict[str, str]]:
        """Get competitor's social media accounts"""
        # This would typically query the database or use search
        # For now, return mock data
        return [
            {'platform': 'twitter', 'username': competitor},
            {'platform': 'instagram', 'username': competitor}
        ]
    
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
