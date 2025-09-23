"""
TikTok API service implementation using TikTok for Business API
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.social_media.base_social_media import BaseSocialMediaAPIService
from app.core.interfaces import SocialMediaMetrics, TrendingContent

logger = logging.getLogger(__name__)


class TikTokAPIService(BaseSocialMediaAPIService):
    """TikTok API service implementation"""
    
    def __init__(self, access_token: str):
        super().__init__(access_token=access_token)
        self.base_url = "https://open-api.tiktok.com"
        self.rate_limit_info = {
            "requests_per_hour": 1000,  # TikTok API limit
            "current_requests": 0,
            "last_reset": datetime.now()
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for TikTok API requests"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'ViralTogether/1.0'
        }
        return headers
    
    def _get_platform_name(self) -> str:
        """Get platform name"""
        return "tiktok"
    
    async def get_user_metrics(self, username: str) -> SocialMediaMetrics:
        """Get user metrics from TikTok"""
        try:
            # Get user info
            user_url = f"{self.base_url}/user/info/"
            params = {
                'fields': 'open_id,union_id,avatar_url,display_name,follower_count,following_count,likes_count,video_count'
            }
            
            user_data = await self._make_request(user_url, params)
            user_info = user_data.get('data', {}).get('user', {})
            
            if not user_info:
                raise Exception(f"User {username} not found")
            
            # Get user's videos for engagement calculation
            videos_url = f"{self.base_url}/video/list/"
            videos_params = {
                'fields': 'id,title,cover_image_url,create_time,share_url,video_description,like_count,comment_count,share_count,view_count',
                'max_count': 20
            }
            
            videos_data = await self._make_request(videos_url, videos_params)
            videos = videos_data.get('data', {}).get('videos', [])
            
            # Calculate engagement metrics
            total_views = sum(int(v.get('view_count', 0)) for v in videos)
            total_likes = sum(int(v.get('like_count', 0)) for v in videos)
            total_comments = sum(int(v.get('comment_count', 0)) for v in videos)
            total_shares = sum(int(v.get('share_count', 0)) for v in videos)
            
            engagement_rate = ((total_likes + total_comments + total_shares) / max(total_views, 1)) * 100
            
            return SocialMediaMetrics(
                platform="tiktok",
                followers=int(user_info.get('follower_count', 0)),
                engagement_rate=engagement_rate,
                reach=total_views,
                impressions=total_views,
                likes=total_likes,
                comments=total_comments,
                shares=total_shares,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get TikTok user metrics: {e}")
            raise
    
    async def get_trending_hashtags(self, platform: str, limit: int = 20) -> List[TrendingContent]:
        """Get trending hashtags from TikTok"""
        try:
            # Get trending hashtags
            hashtags_url = f"{self.base_url}/discover/hashtag/"
            params = {
                'count': limit
            }
            
            hashtags_data = await self._make_request(hashtags_url, params)
            hashtags = hashtags_data.get('data', {}).get('hashtags', [])
            
            trending_content = []
            for hashtag in hashtags:
                trending_content.append(TrendingContent(
                    platform="tiktok",
                    hashtag=f"#{hashtag.get('name', '')}",
                    post_count=int(hashtag.get('video_count', 0)),
                    engagement_rate=float(hashtag.get('engagement_rate', 0.0)),
                    trend_score=float(hashtag.get('trend_score', 0.0)),
                    category=hashtag.get('category', 'general'),
                    timestamp=datetime.now()
                ))
            
            return trending_content
            
        except Exception as e:
            logger.error(f"Failed to get TikTok trending hashtags: {e}")
            return []
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a specific TikTok video"""
        try:
            video_url = f"{self.base_url}/video/query/"
            params = {
                'video_id': post_id,
                'fields': 'id,title,cover_image_url,create_time,share_url,video_description,like_count,comment_count,share_count,view_count'
            }
            
            video_data = await self._make_request(video_url, params)
            video = video_data.get('data', {}).get('video', {})
            
            if not video:
                raise Exception(f"Video {post_id} not found")
            
            view_count = int(video.get('view_count', 0))
            like_count = int(video.get('like_count', 0))
            comment_count = int(video.get('comment_count', 0))
            share_count = int(video.get('share_count', 0))
            
            engagement_rate = ((like_count + comment_count + share_count) / max(view_count, 1)) * 100
            
            return {
                'video_id': post_id,
                'title': video.get('title'),
                'views': view_count,
                'likes': like_count,
                'comments': comment_count,
                'shares': share_count,
                'engagement_rate': engagement_rate,
                'created_at': video.get('create_time'),
                'description': video.get('video_description')
            }
            
        except Exception as e:
            logger.error(f"Failed to get TikTok video analytics: {e}")
            raise
    
    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for TikTok videos"""
        try:
            search_url = f"{self.base_url}/video/search/"
            params = {
                'query': query,
                'count': min(limit, 20),
                'fields': 'id,title,cover_image_url,create_time,share_url,video_description,like_count,comment_count,share_count,view_count'
            }
            
            search_data = await self._make_request(search_url, params)
            videos = search_data.get('data', {}).get('videos', [])
            
            results = []
            for video in videos:
                results.append({
                    'video_id': video.get('id'),
                    'title': video.get('title'),
                    'description': video.get('video_description'),
                    'views': int(video.get('view_count', 0)),
                    'likes': int(video.get('like_count', 0)),
                    'comments': int(video.get('comment_count', 0)),
                    'shares': int(video.get('share_count', 0)),
                    'created_at': video.get('create_time'),
                    'thumbnail': video.get('cover_image_url')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search TikTok videos: {e}")
            return []
