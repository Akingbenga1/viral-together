"""
Twitter API service implementation using free endpoints
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.social_media.base_social_media import BaseSocialMediaAPIService
from app.core.interfaces import SocialMediaMetrics, TrendingContent

logger = logging.getLogger(__name__)


class TwitterAPIService(BaseSocialMediaAPIService):
    """Twitter API service implementation"""
    
    def __init__(self, bearer_token: str):
        super().__init__(access_token=bearer_token)
        self.base_url = "https://api.twitter.com/2"
        self.rate_limit_info = {
            "requests_per_hour": 300,  # Free tier limit
            "current_requests": 0,
            "last_reset": datetime.now()
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Twitter API requests"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'ViralTogether/1.0'
        }
        return headers
    
    def _get_platform_name(self) -> str:
        """Get platform name"""
        return "twitter"
    
    async def get_user_metrics(self, username: str) -> SocialMediaMetrics:
        """Get user metrics from Twitter"""
        try:
            # Get user by username
            user_url = f"{self.base_url}/users/by/username/{username}"
            user_params = {
                'user.fields': 'public_metrics,verified,created_at'
            }
            
            user_data = await self._make_request(user_url, user_params)
            user = user_data.get('data', {})
            
            if not user:
                raise Exception(f"User {username} not found")
            
            # Get recent tweets for engagement calculation
            tweets_url = f"{self.base_url}/users/{user['id']}/tweets"
            tweets_params = {
                'max_results': 10,
                'tweet.fields': 'public_metrics,created_at'
            }
            
            tweets_data = await self._make_request(tweets_url, tweets_params)
            tweets = tweets_data.get('data', [])
            
            # Calculate engagement rate
            total_engagement = 0
            total_impressions = 0
            
            for tweet in tweets:
                metrics = tweet.get('public_metrics', {})
                total_engagement += (
                    metrics.get('like_count', 0) +
                    metrics.get('retweet_count', 0) +
                    metrics.get('reply_count', 0)
                )
                total_impressions += metrics.get('impression_count', 0)
            
            engagement_rate = (total_engagement / max(total_impressions, 1)) * 100
            
            return SocialMediaMetrics(
                platform="twitter",
                followers=user.get('public_metrics', {}).get('followers_count', 0),
                engagement_rate=engagement_rate,
                reach=user.get('public_metrics', {}).get('followers_count', 0),
                impressions=total_impressions,
                likes=sum(t.get('public_metrics', {}).get('like_count', 0) for t in tweets),
                comments=sum(t.get('public_metrics', {}).get('reply_count', 0) for t in tweets),
                shares=sum(t.get('public_metrics', {}).get('retweet_count', 0) for t in tweets),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get Twitter user metrics: {e}")
            raise
    
    async def get_trending_hashtags(self, platform: str, limit: int = 20) -> List[TrendingContent]:
        """Get trending hashtags from Twitter"""
        logger.info(f"Starting Twitter trending hashtags request for {platform} with limit {limit}")
        try:
            # Use Twitter's trending topics endpoint
            trends_url = f"{self.base_url}/trends/by/woeid/1"  # Worldwide trends
            logger.info(f"Calling Twitter API: {trends_url}")
            
            trends_data = await self._make_request(trends_url)
            trends = trends_data.get('trends', [])
            logger.info(f"Twitter API response: {len(trends)} trends found")
            
            trending_content = []
            logger.info(f"Processing {len(trends[:limit])} Twitter trends into TrendingContent objects")
            for trend in trends[:limit]:
                trending_content.append(TrendingContent(
                    platform="twitter",
                    hashtag=trend.get('name', ''),
                    post_count=trend.get('tweet_volume', 0),
                    engagement_rate=0.0,  # Not available in trends API
                    trend_score=trend.get('tweet_volume', 0) / 1000,  # Normalize
                    category="trending",
                    timestamp=datetime.now()
                ))
            
            logger.info(f"Successfully processed {len(trending_content)} Twitter trending hashtags")
            return trending_content
            
        except Exception as e:
            logger.error(f"Failed to get Twitter trending hashtags: {e}")
            return []
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a specific tweet"""
        try:
            tweet_url = f"{self.base_url}/tweets/{post_id}"
            params = {
                'tweet.fields': 'public_metrics,created_at,author_id'
            }
            
            tweet_data = await self._make_request(tweet_url, params)
            tweet = tweet_data.get('data', {})
            
            if not tweet:
                raise Exception(f"Tweet {post_id} not found")
            
            metrics = tweet.get('public_metrics', {})
            
            return {
                'tweet_id': post_id,
                'likes': metrics.get('like_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0),
                'impressions': metrics.get('impression_count', 0),
                'engagement_rate': self._calculate_engagement_rate(metrics),
                'created_at': tweet.get('created_at'),
                'author_id': tweet.get('author_id')
            }
            
        except Exception as e:
            logger.error(f"Failed to get Twitter post analytics: {e}")
            raise
    
    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tweets"""
        try:
            search_url = f"{self.base_url}/tweets/search/recent"
            params = {
                'query': query,
                'max_results': min(limit, 100),
                'tweet.fields': 'public_metrics,created_at,author_id'
            }
            
            search_data = await self._make_request(search_url, params)
            tweets = search_data.get('data', [])
            
            results = []
            for tweet in tweets:
                metrics = tweet.get('public_metrics', {})
                results.append({
                    'tweet_id': tweet.get('id'),
                    'text': tweet.get('text'),
                    'author_id': tweet.get('author_id'),
                    'created_at': tweet.get('created_at'),
                    'likes': metrics.get('like_count', 0),
                    'retweets': metrics.get('retweet_count', 0),
                    'replies': metrics.get('reply_count', 0),
                    'engagement_rate': self._calculate_engagement_rate(metrics)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search Twitter posts: {e}")
            return []
    
    def _calculate_engagement_rate(self, metrics: Dict[str, Any]) -> float:
        """Calculate engagement rate from metrics"""
        total_engagement = (
            metrics.get('like_count', 0) +
            metrics.get('retweet_count', 0) +
            metrics.get('reply_count', 0)
        )
        impressions = metrics.get('impression_count', 0)
        
        if impressions == 0:
            return 0.0
        
        return (total_engagement / impressions) * 100
