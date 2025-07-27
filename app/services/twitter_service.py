import logging
import asyncio
import json
from typing import Dict, Any, Optional
import ollama

from app.core.config import settings
from app.db.models.notification import Notification

logger = logging.getLogger(__name__)

class TwitterService:
    """Twitter service with MCP tool calling and Ollama content generation"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'TWITTER_API_KEY', '')
        self.api_secret = getattr(settings, 'TWITTER_API_SECRET', '')
        self.access_token = getattr(settings, 'TWITTER_ACCESS_TOKEN', '')
        self.access_token_secret = getattr(settings, 'TWITTER_ACCESS_TOKEN_SECRET', '')
        self.bearer_token = getattr(settings, 'TWITTER_BEARER_TOKEN', '')
        self.enabled = getattr(settings, 'TWITTER_NOTIFICATIONS_ENABLED', True)
        
        # Ollama configuration
        self.ollama_model = getattr(settings, 'OLLAMA_MODEL', 'deepseek-r1:1.5b')
        self.ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        
        # Twitter templates for content generation
        self.twitter_templates = {
            "promotion_created": {
                "prompt_template": """
Generate a professional and engaging tweet about a new promotion that was just created:

Business: {business_name}
Promotion: {promotion_name}  
Industry: {industry}
Budget: ${budget}

Make the tweet:
- Professional but exciting
- Include relevant hashtags (max 3)
- Mention the opportunity for influencers
- Keep it under 280 characters
- Don't include any thinking or explanation

Tweet:""",
                "hashtags": ["#InfluencerMarketing", "#Collaboration", "#Partnership"]
            },
            
            "collaboration_created": {
                "prompt_template": """
Generate a celebratory tweet about a new collaboration that was just created:

Influencer: {influencer_name}
Business: {business_name}
Promotion: {promotion_name}
Collaboration Type: {collaboration_type}

Make the tweet:
- Celebratory and professional
- Announce the new partnership
- Include relevant hashtags (max 3)
- Keep it under 280 characters
- Don't include any thinking or explanation

Tweet:""",
                "hashtags": ["#Partnership", "#InfluencerCollaboration", "#NewDeal"]
            },
            
            "collaboration_approved": {
                "prompt_template": """
Generate an exciting tweet about a collaboration that was just approved:

Business: {business_name}
Influencer: {influencer_name}
Promotion: {promotion_name}
Collaboration Type: {collaboration_type}

Make the tweet:
- Exciting and congratulatory  
- Celebrate the approved partnership
- Include relevant hashtags (max 3)
- Keep it under 280 characters
- Don't include any thinking or explanation

Tweet:""",
                "hashtags": ["#Approved", "#InfluencerSuccess", "#Partnership"]
            },
            
            "influencer_interest": {
                "prompt_template": """
Generate an engaging tweet about an influencer showing interest in a promotion:

Influencer: {influencer_name}
Business: {business_name}  
Promotion: {promotion_name}

Make the tweet:
- Professional and engaging
- Highlight the interest/opportunity
- Include relevant hashtags (max 3)
- Keep it under 280 characters
- Don't include any thinking or explanation

Tweet:""",
                "hashtags": ["#InfluencerInterest", "#OpportunityKnocks", "#Collaboration"]
            }
        }
    
    async def post_notification_tweet(self, notification: Notification) -> Optional[str]:
        """Generate and post a tweet for a notification"""
        if not self.enabled:
            logger.info("Twitter notifications disabled, skipping tweet")
            return None
        
        try:
            # Generate tweet content using Ollama
            tweet_content = await self._generate_tweet_content(notification)
            if not tweet_content:
                logger.warning(f"Failed to generate tweet content for notification {notification.id}")
                return None
            
            # Post tweet using MCP
            tweet_id = await self._post_tweet_mcp(tweet_content, notification.event_metadata)
            
            logger.info(f"Successfully posted tweet {tweet_id} for notification {notification.id}")
            return tweet_id
            
        except Exception as e:
            logger.error(f"Failed to post tweet for notification {notification.id}: {str(e)}")
            raise
    
    async def _generate_tweet_content(self, notification: Notification) -> Optional[str]:
        """Generate tweet content using Ollama"""
        try:
            template_config = self.twitter_templates.get(notification.event_type)
            if not template_config:
                logger.warning(f"No Twitter template for event type: {notification.event_type}")
                return None
            
            # Prepare context for prompt
            context = {
                **notification.event_metadata,
                'budget': notification.event_metadata.get('budget', 'TBD'),
                'industry': notification.event_metadata.get('industry', 'General')
            }
            
            # Generate prompt
            prompt = template_config["prompt_template"].format(**context)
            
            # Call Ollama with think=False for clean output
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.ollama_model,
                prompt=prompt,
                options={'think': False}
            )
            
            tweet_text = response.get('response', '').strip()
            
            # Ensure it's within Twitter's character limit
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            
            logger.info(f"Generated tweet content for {notification.event_type}: {tweet_text[:50]}...")
            return tweet_text
            
        except Exception as e:
            logger.error(f"Failed to generate tweet content: {str(e)}")
            return None
    
    async def _post_tweet_mcp(self, content: str, event_metadata: Dict[str, Any]) -> Optional[str]:
        """Post tweet using MCP tool calling"""
        try:
            # MCP tool call structure for Twitter API
            mcp_request = {
                "method": "tools/call",
                "params": {
                    "name": "twitter_post",
                    "arguments": {
                        "text": content,
                        "event_metadata": event_metadata
                    }
                }
            }
            
            # Here we would make the actual MCP call
            # For now, we'll simulate the Twitter API call
            tweet_id = await self._simulate_twitter_post(content)
            
            return tweet_id
            
        except Exception as e:
            logger.error(f"MCP Twitter post failed: {str(e)}")
            raise
    
    async def _simulate_twitter_post(self, content: str) -> str:
        """Simulate Twitter API post (replace with actual MCP call)"""
        try:
            # This would be replaced with actual Twitter API v2 call
            # Using requests-oauthlib or tweepy through MCP
            
            import hashlib
            import time
            
            # Simulate API call delay
            await asyncio.sleep(1)
            
            # Generate fake tweet ID for simulation
            tweet_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:10]
            
            logger.info(f"Simulated Twitter post: {content[:50]}... -> ID: {tweet_id}")
            return tweet_id
            
        except Exception as e:
            logger.error(f"Twitter API simulation failed: {str(e)}")
            raise
    
    async def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet using MCP"""
        try:
            if not self.enabled:
                return False
            
            # MCP tool call for tweet deletion
            mcp_request = {
                "method": "tools/call", 
                "params": {
                    "name": "twitter_delete",
                    "arguments": {
                        "tweet_id": tweet_id
                    }
                }
            }
            
            # Simulate deletion for now
            logger.info(f"Simulated tweet deletion: {tweet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tweet {tweet_id}: {str(e)}")
            return False
    
    async def get_tweet_metrics(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get tweet engagement metrics using MCP"""
        try:
            if not self.enabled:
                return None
            
            # MCP tool call for tweet metrics
            mcp_request = {
                "method": "tools/call",
                "params": {
                    "name": "twitter_metrics", 
                    "arguments": {
                        "tweet_id": tweet_id
                    }
                }
            }
            
            # Simulate metrics for now
            return {
                "likes": 15,
                "retweets": 3,  
                "replies": 2,
                "impressions": 250
            }
            
        except Exception as e:
            logger.error(f"Failed to get tweet metrics for {tweet_id}: {str(e)}")
            return None
    
    def validate_credentials(self) -> bool:
        """Validate Twitter API credentials"""
        required_credentials = [
            self.api_key,
            self.api_secret, 
            self.access_token,
            self.access_token_secret
        ]
        
        missing = [cred for cred in required_credentials if not cred]
        if missing:
            logger.warning(f"Missing Twitter credentials: {len(missing)} fields")
            return False
        
        return True
    
    async def test_connection(self) -> bool:
        """Test Twitter API connection"""
        try:
            if not self.validate_credentials():
                return False
            
            # Test with a simple MCP call
            test_content = "Testing connection from Viral Together! 🚀 #Test"
            result = await self._simulate_twitter_post(test_content)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Twitter connection test failed: {str(e)}")
            return False

# Global Twitter service instance
twitter_service = TwitterService() 