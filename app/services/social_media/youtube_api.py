"""
YouTube API service implementation using YouTube Data API v3
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.social_media.base_social_media import BaseSocialMediaAPIService
from app.core.interfaces import SocialMediaMetrics, TrendingContent

logger = logging.getLogger(__name__)


class YouTubeAPIService(BaseSocialMediaAPIService):
    """YouTube API service implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.rate_limit_info = {
            "requests_per_day": 10000,  # YouTube API quota
            "current_requests": 0,
            "last_reset": datetime.now()
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for YouTube API requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ViralTogether/1.0'
        }
        return headers
    
    def _get_platform_name(self) -> str:
        """Get platform name"""
        return "youtube"
    
    async def get_user_metrics(self, username: str) -> SocialMediaMetrics:
        """Get user metrics from YouTube"""
        try:
            # Get channel by username
            search_url = f"{self.base_url}/search"
            search_params = {
                'key': self.api_key,
                'part': 'snippet',
                'type': 'channel',
                'q': username,
                'maxResults': 1
            }
            
            search_data = await self._make_request(search_url, search_params)
            channels = search_data.get('items', [])
            
            if not channels:
                raise Exception(f"Channel {username} not found")
            
            channel_id = channels[0]['id']['channelId']
            
            # Get channel statistics
            channel_url = f"{self.base_url}/channels"
            channel_params = {
                'key': self.api_key,
                'part': 'statistics',
                'id': channel_id
            }
            
            channel_data = await self._make_request(channel_url, channel_params)
            channel = channel_data.get('items', [{}])[0]
            stats = channel.get('statistics', {})
            
            # Get recent videos for engagement calculation
            videos_url = f"{self.base_url}/search"
            videos_params = {
                'key': self.api_key,
                'part': 'snippet',
                'channelId': channel_id,
                'type': 'video',
                'maxResults': 10,
                'order': 'date'
            }
            
            videos_data = await self._make_request(videos_url, videos_params)
            video_ids = [item['id']['videoId'] for item in videos_data.get('items', [])]
            
            # Get video statistics
            if video_ids:
                video_stats_url = f"{self.base_url}/videos"
                video_stats_params = {
                    'key': self.api_key,
                    'part': 'statistics',
                    'id': ','.join(video_ids)
                }
                
                video_stats_data = await self._make_request(video_stats_url, video_stats_params)
                videos = video_stats_data.get('items', [])
                
                total_views = sum(int(v.get('statistics', {}).get('viewCount', 0)) for v in videos)
                total_likes = sum(int(v.get('statistics', {}).get('likeCount', 0)) for v in videos)
                total_comments = sum(int(v.get('statistics', {}).get('commentCount', 0)) for v in videos)
                
                engagement_rate = ((total_likes + total_comments) / max(total_views, 1)) * 100
            else:
                engagement_rate = 0.0
                total_likes = 0
                total_comments = 0
            
            return SocialMediaMetrics(
                platform="youtube",
                followers=int(stats.get('subscriberCount', 0)),
                engagement_rate=engagement_rate,
                reach=int(stats.get('viewCount', 0)),
                impressions=int(stats.get('viewCount', 0)),
                likes=total_likes,
                comments=total_comments,
                shares=0,  # Not available in YouTube API
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get YouTube user metrics: {e}")
            raise
    
    async def get_trending_hashtags(self, platform: str, limit: int = 20) -> List[TrendingContent]:
        """Get trending hashtags from YouTube"""
        try:
            # Get trending videos
            trending_url = f"{self.base_url}/videos"
            trending_params = {
                'key': self.api_key,
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': 'US',
                'maxResults': limit
            }
            
            trending_data = await self._make_request(trending_url, trending_params)
            videos = trending_data.get('items', [])
            
            trending_content = []
            for video in videos:
                snippet = video.get('snippet', {})
                stats = video.get('statistics', {})
                
                # Extract hashtags from description
                description = snippet.get('description', '')
                hashtags = [tag for tag in description.split() if tag.startswith('#')]
                
                for hashtag in hashtags[:3]:  # Limit hashtags per video
                    view_count = int(stats.get('viewCount', 0))
                    like_count = int(stats.get('likeCount', 0))
                    comment_count = int(stats.get('commentCount', 0))
                    
                    engagement_rate = ((like_count + comment_count) / max(view_count, 1)) * 100
                    trend_score = view_count / 1000000  # Normalize by millions
                    
                    trending_content.append(TrendingContent(
                        platform="youtube",
                        hashtag=hashtag,
                        post_count=1,
                        engagement_rate=engagement_rate,
                        trend_score=trend_score,
                        category=snippet.get('categoryId', 'general'),
                        timestamp=datetime.now()
                    ))
            
            return trending_content[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get YouTube trending hashtags: {e}")
            return []
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a specific YouTube video"""
        try:
            video_url = f"{self.base_url}/videos"
            params = {
                'key': self.api_key,
                'part': 'snippet,statistics',
                'id': post_id
            }
            
            video_data = await self._make_request(video_url, params)
            videos = video_data.get('items', [])
            
            if not videos:
                raise Exception(f"Video {post_id} not found")
            
            video = videos[0]
            snippet = video.get('snippet', {})
            stats = video.get('statistics', {})
            
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            comment_count = int(stats.get('commentCount', 0))
            
            engagement_rate = ((like_count + comment_count) / max(view_count, 1)) * 100
            
            return {
                'video_id': post_id,
                'title': snippet.get('title'),
                'views': view_count,
                'likes': like_count,
                'comments': comment_count,
                'engagement_rate': engagement_rate,
                'published_at': snippet.get('publishedAt'),
                'channel_id': snippet.get('channelId'),
                'category_id': snippet.get('categoryId')
            }
            
        except Exception as e:
            logger.error(f"Failed to get YouTube video analytics: {e}")
            raise
    
    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for YouTube videos"""
        try:
            search_url = f"{self.base_url}/search"
            params = {
                'key': self.api_key,
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': min(limit, 50),
                'order': 'relevance'
            }
            
            search_data = await self._make_request(search_url, params)
            videos = search_data.get('items', [])
            
            results = []
            for video in videos:
                snippet = video.get('snippet', {})
                results.append({
                    'video_id': video.get('id', {}).get('videoId'),
                    'title': snippet.get('title'),
                    'description': snippet.get('description'),
                    'channel_title': snippet.get('channelTitle'),
                    'published_at': snippet.get('publishedAt'),
                    'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search YouTube videos: {e}")
            return []
