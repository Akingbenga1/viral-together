import asyncio
import logging
from typing import Optional, Dict, Any
import json
import time
import traceback
from datetime import datetime

from app.core.config import settings
from app.db.models.notification import Notification
from app.services.mcp_client import SimpleMCPClient

logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self._validate_config()
        self.mcp_client = SimpleMCPClient(config_file="mcp_config.json")
        
        # 🔍 DISCOVER AVAILABLE TOOLS FOR DEBUGGING
        logger.info("🔍 TWITTER_SERVICE_INIT: Discovering available MCP tools...")
        # Note: Tool discovery will be done async when first needed

    def _validate_config(self):
        """Validate Twitter configuration and log setup details"""
        logger.info(f"🐦 TWITTER_SERVICE_INIT: Initializing Twitter service")
        logger.info(f"🐦 TWITTER_CONFIG: enabled={settings.TWITTER_NOTIFICATIONS_ENABLED}, model={settings.OLLAMA_MODEL}")
        
        if not settings.TWITTER_NOTIFICATIONS_ENABLED:
            logger.warning(f"⚠️ TWITTER_DISABLED: Twitter notifications are disabled in configuration")
            return
            
        # Check credentials
        credentials = [
            ("API_KEY", settings.TWITTER_API_KEY),
            ("API_SECRET", settings.TWITTER_API_SECRET),
            ("ACCESS_TOKEN", settings.TWITTER_ACCESS_TOKEN),
            ("ACCESS_TOKEN_SECRET", settings.TWITTER_ACCESS_TOKEN_SECRET),
            ("BEARER_TOKEN", settings.TWITTER_BEARER_TOKEN)
        ]
        
        missing = [name for name, value in credentials if not value]
        if missing:
            logger.warning(f"⚠️ TWITTER_CREDENTIALS_MISSING: {len(missing)} credentials missing: {missing}")
        else:
            logger.info(f"✅ TWITTER_CREDENTIALS_OK: All Twitter credentials configured")

    async def post_notification_tweet(self, notification: Notification) -> Optional[str]:
        """Post notification tweet with comprehensive monitoring"""
        start_time = time.time()
        
        logger.info(f"🐦 TWITTER_POST_START: notification={notification.id}, event_type={notification.event_type}")
        logger.debug(f"🐦 TWITTER_CONTEXT: title='{notification.title}', metadata_keys={list(notification.event_metadata.keys()) if notification.event_metadata else []}")

        if not settings.TWITTER_NOTIFICATIONS_ENABLED:
            logger.info(f"⚠️ TWITTER_SKIPPED: Twitter notifications disabled, skipping notification {notification.id}")
            return None

        try:
            # 🔍 FIRST: Discover available tools for debugging
            logger.debug(f"🔍 TWITTER_DISCOVERING_TOOLS: Checking what MCP tools are available")
            available_tools = await self.discover_available_tools()
            
            # Generate tweet content (keep existing Ollama logic)
            content_start_time = time.time()
            logger.debug(f"🐦 TWITTER_CONTENT_START: Generating tweet content")
            
            tweet_content = await self._generate_tweet_content(notification)
            
            if not tweet_content:
                logger.warning(f"⚠️ TWITTER_CONTENT_EMPTY: No content generated for notification {notification.id}")
                return None

            content_time = time.time() - content_start_time
            logger.info(f"🐦 TWITTER_CONTENT_SUCCESS: time={content_time:.3f}s, length={len(tweet_content)}, preview='{tweet_content[:50]}...'")

            # Post tweet via MCP (updated to use real MCP client)
            post_start_time = time.time()
            logger.debug(f"🐦 TWITTER_API_START: Posting tweet via MCP tool")
            
            tweet_id = await self._post_tweet_via_mcp(tweet_content, notification)
            
            post_time = time.time() - post_start_time
            total_time = time.time() - start_time
            
            if tweet_id:
                logger.info(f"✅ TWITTER_POST_SUCCESS: notification={notification.id}, tweet_id={tweet_id}")
                logger.info(f"📊 TWITTER_METRICS: content_time={content_time:.3f}s, post_time={post_time:.3f}s, total_time={total_time:.3f}s")
                return tweet_id
            else:
                raise Exception("Tweet ID not returned from MCP tool")

        except Exception as e:
            total_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ TWITTER_POST_FAILURE: notification={notification.id}, time={total_time:.3f}s")
            logger.error(f"Twitter error details: {error_msg}")
            logger.error(f"Twitter stack trace: {traceback.format_exc()}")
            raise

    async def _generate_tweet_content(self, notification: Notification) -> Optional[str]:
        """Generate tweet content using Ollama with comprehensive logging"""
        start_time = time.time()
        logger.info(f"🤖 OLLAMA_CONTENT_START: Generating tweet content for {notification.event_type}")
        
        try:
            # Get template for event type
            template = self._get_tweet_template(notification.event_type)
            if not template:
                logger.warning(f"⚠️ TWITTER_TEMPLATE_MISSING: No template for event type: {notification.event_type}")
                return None

            logger.debug(f"🤖 OLLAMA_TEMPLATE: Using template for {notification.event_type}")
            
            # Prepare context for template
            context = {
                "notification": notification,
                "event_metadata": notification.event_metadata or {},
                "title": notification.title,
                "message": notification.message
            }
            
            logger.debug(f"🤖 OLLAMA_CONTEXT: context_keys={list(context.keys())}")
            
            # Fill template with notification data
            filled_template = template.format(**context.get("event_metadata", {}))
            logger.debug(f"🤖 OLLAMA_TEMPLATE_FILLED: '{filled_template}'")

            # Special handling for influencer_interest: use template only (no Ollama)
            if notification.event_type == 'influencer_interest':
                logger.info(f"📝 TEMPLATE_ONLY: Using template-only approach for {notification.event_type}")
                
                # Validate template length
                if len(filled_template) > 280:
                    logger.warning(f"⚠️ TWITTER_LENGTH_WARNING: Template too long ({len(filled_template)} chars), truncating")
                    filled_template = filled_template[:277] + "..."
                
                total_time = time.time() - start_time
                logger.info(f"✅ TWITTER_CONTENT_COMPLETE: time={total_time:.3f}s, template_only=True, final_length={len(filled_template)}")
                
                return filled_template

            # Use Ollama to enhance/finalize content for other event types
            ollama_start_time = time.time()
            logger.debug(f"🤖 OLLAMA_API_START: Calling Ollama with model {settings.OLLAMA_MODEL}")
            
            try:
                import ollama
                
                prompt = f"""You must create a tweet that follows this EXACT template structure:

REQUIRED TEMPLATE: {filled_template}

STRICT RULES:
- Keep the exact same structure and flow
- Only enhance the language slightly for engagement
- Keep all emojis and hashtags from the template
- Do NOT change the core message or structure
- MAXIMUM 280 characters (strictly enforce this limit)
- Do NOT include any thinking, reasoning, or explanation
- Return ONLY the final tweet text
- No additional commentary or analysis

Enhanced tweet:"""

                logger.debug(f"🤖 OLLAMA_PROMPT: Sending strict template adherence prompt to model")
                
                response = ollama.chat(
                    model=settings.OLLAMA_MODEL,
                    messages=[{
                        'role': 'user', 
                        'content': prompt
                    }],
                    think=False  # Ensure no thinking output
                )
                
                ollama_time = time.time() - ollama_start_time
                tweet_text = response['message']['content'].strip()
                
                logger.info(f"🤖 OLLAMA_SUCCESS: time={ollama_time:.3f}s, length={len(tweet_text)}")
                logger.debug(f"🤖 OLLAMA_RESPONSE: '{tweet_text}'")

                # Validate tweet length
                if len(tweet_text) > 280:
                    logger.warning(f"⚠️ TWITTER_LENGTH_WARNING: Tweet too long ({len(tweet_text)} chars), truncating")
                    tweet_text = tweet_text[:277] + "..."

                total_time = time.time() - start_time
                logger.info(f"✅ TWITTER_CONTENT_COMPLETE: time={total_time:.3f}s, final_length={len(tweet_text)}")
                
                return tweet_text

            except ImportError:
                logger.error(f"❌ OLLAMA_IMPORT_ERROR: Ollama library not available")
                # Fallback to template only
                logger.info(f"🔄 TWITTER_FALLBACK: Using template without Ollama enhancement")
                return filled_template[:280]
                
            except Exception as e:
                ollama_time = time.time() - ollama_start_time
                logger.error(f"❌ OLLAMA_API_ERROR: time={ollama_time:.3f}s, error={str(e)}")
                # Fallback to template
                logger.info(f"🔄 TWITTER_FALLBACK: Using template due to Ollama error")
                return filled_template[:280]

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ TWITTER_CONTENT_FAILURE: time={total_time:.3f}s, error={str(e)}")
            logger.error(f"Content generation stack trace: {traceback.format_exc()}")
            return None

    def _get_tweet_template(self, event_type: str) -> Optional[str]:
        """Get tweet template for event type with logging"""
        logger.debug(f"🐦 TEMPLATE_LOOKUP: Finding template for {event_type}")
        
        templates = {
            'promotion_created': "🎯 New promotion alert! {business_name} has launched '{promotion_name}' - great opportunity for influencers! 💼✨ #InfluencerOpportunity #Collaboration",
            'collaboration_created': "🤝 New collaboration request from {business_name}! Check out this exciting opportunity with {promotion_name} 🚀 #Partnership #InfluencerLife",
            'collaboration_approved': "🎉 Collaboration approved! {influencer_name} is now partnering with {business_name} on {promotion_name} - exciting things ahead! 💫 #Success #Partnership",
            'influencer_interest': "👀 {influencer_name} is interested in '{promotion_name}' by {business_name} - great match! 🎯 https://viraltogether.com/promotions/{promotion_id} #InfluencerMarketing"
        }
        
        template = templates.get(event_type)
        
        if template:
            logger.debug(f"✅ TEMPLATE_FOUND: Template located for {event_type}")
        else:
            logger.warning(f"⚠️ TEMPLATE_MISSING: No template found for {event_type}")
            
        return template

    async def _post_tweet_via_mcp(self, content: str, notification: Notification) -> Optional[str]:
        """Post tweet via MCP tool with real implementation (single attempt)"""
        start_time = time.time()
        logger.info(f"🔧 MCP_POST_START: Posting via MCP tool")
        logger.debug(f"🔧 MCP_CONTENT: '{content}'")

        try:
            # Real MCP tool call using our SimpleMCPClient
            logger.debug(f"🔧 MCP_TOOL_CALL: Calling Twitter MCP server")
            
            # Use primary tool name only (single attempt)
            tool_name = "post_tweet"
            logger.debug(f"🔧 MCP_SINGLE_TOOL: Using tool '{tool_name}'")
            
            result = await self.mcp_client.call_tool(
                server="twitter-tools",
                tool=tool_name, 
                arguments={
                    "content": content,
                    "text": content,  # Alternative argument name
                    "metadata": notification.event_metadata or {}
                }
            )
            
            logger.info(f"✅ MCP_TOOL_SUCCESS: {tool_name} completed successfully!")
            logger.info(f"🔧 MCP_TOOL_CALL: Result: {result}")
            
            # Method 1: Extract tweet ID from URL in content text field
            tweet_id = None
            
            if 'content' in result and result['content']:
                # Get text content from the first content item
                text_content = result['content'][0].get('text', '') if result['content'] else ''
                logger.debug(f"🔧 MCP_TEXT_CONTENT: {text_content}")
                
                # Extract tweet ID from Twitter URL using regex
                import re
                url_match = re.search(r'https://twitter\.com/status/(\d+)', text_content)
                if url_match:
                    tweet_id = url_match.group(1)
                    logger.info(f"✅ MCP_TWEET_ID_EXTRACTED: Found tweet_id={tweet_id} from URL")
                else:
                    logger.warning(f"⚠️ MCP_NO_URL_MATCH: No Twitter URL found in response text")
                    
                # Also check for success confirmation
                if 'Tweet posted successfully!' in text_content:
                    logger.info(f"✅ MCP_POST_CONFIRMED: Tweet posting confirmed by server")
                else:
                    logger.warning(f"⚠️ MCP_NO_SUCCESS_MSG: No success confirmation found in response")
            else:
                logger.warning(f"⚠️ MCP_NO_CONTENT: No 'content' field found in MCP response")
                logger.debug(f"🔧 MCP_RESPONSE_KEYS: Available keys: {list(result.keys())}")
            
            if not tweet_id:
                raise Exception("No tweet_id could be extracted from MCP server response")
            
            mcp_time = time.time() - start_time
            logger.info(f"✅ MCP_POST_SUCCESS: time={mcp_time:.3f}s, tweet_id={tweet_id}")
            logger.debug(f"🔧 MCP_RESPONSE: {result}")
            
            return tweet_id

        except Exception as e:
            mcp_time = time.time() - start_time
            logger.error(f"❌ MCP_POST_FAILURE: time={mcp_time:.3f}s")
            logger.error(f"MCP error details: {str(e)}")
            logger.error(f"MCP stack trace: {traceback.format_exc()}")
            raise

    # Additional monitoring methods
    async def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet with logging"""
        logger.info(f"🗑️ TWITTER_DELETE_START: Deleting tweet {tweet_id}")
        
        try:
            # Use MCP client for tweet deletion
            result = await self.mcp_client.call_tool(
                server="twitter-tools",
                tool="delete_tweet",
                arguments={"tweet_id": tweet_id}
            )
            logger.info(f"✅ TWITTER_DELETE_SUCCESS: tweet_id={tweet_id}")
            return result.get("success", True)
            
        except Exception as e:
            logger.error(f"❌ TWITTER_DELETE_FAILURE: tweet_id={tweet_id}, error={str(e)}")
            raise

    async def get_tweet_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """Get tweet metrics with logging"""
        logger.info(f"📊 TWITTER_METRICS_START: Getting metrics for tweet {tweet_id}")
        
        try:
            # Use MCP client for metrics retrieval
            result = await self.mcp_client.call_tool(
                server="twitter-tools",
                tool="get_tweet_metrics",
                arguments={"tweet_id": tweet_id}
            )
            
            logger.info(f"✅ TWITTER_METRICS_SUCCESS: tweet_id={tweet_id}, metrics={result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ TWITTER_METRICS_FAILURE: tweet_id={tweet_id}, error={str(e)}")
            raise

    async def discover_available_tools(self) -> Dict[str, Any]:
        """Discover what tools are available from the Twitter MCP server"""
        logger.info("🔍 TWITTER_TOOL_DISCOVERY: Checking available MCP tools...")
        
        try:
            tools = await self.mcp_client.list_tools("twitter-tools")
            logger.info(f"✅ TWITTER_TOOLS_FOUND: {tools}")
            return tools
        except Exception as e:
            logger.error(f"❌ TWITTER_TOOL_DISCOVERY_FAILED: {str(e)}")
            return {}

    def validate_credentials(self) -> bool:
        """Validate Twitter API credentials with logging"""
        logger.info(f"🔐 TWITTER_CREDENTIALS_CHECK: Validating API credentials")
        
        try:
            required_credentials = [
                settings.TWITTER_API_KEY,
                settings.TWITTER_API_SECRET,
                settings.TWITTER_ACCESS_TOKEN,
                settings.TWITTER_ACCESS_TOKEN_SECRET
            ]
            
            missing_count = sum(1 for cred in required_credentials if not cred)
            
            if missing_count == 0:
                logger.info(f"✅ TWITTER_CREDENTIALS_VALID: All credentials configured")
                return True
            else:
                logger.error(f"❌ TWITTER_CREDENTIALS_INVALID: {missing_count} credentials missing")
                return False
                
        except Exception as e:
            logger.error(f"❌ TWITTER_CREDENTIALS_ERROR: {str(e)}")
            return False

# Global service instance
twitter_service = TwitterService() 