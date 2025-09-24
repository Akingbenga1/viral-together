"""
Enhanced AI Agent Service with real-time data integration
"""

import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.interfaces import IAIAgentService
from app.services.web_search.web_search_factory import WebSearchFactory
from app.services.social_media.social_media_factory import SocialMediaFactory
from app.services.analytics.real_time_analytics import RealTimeAnalyticsService
from app.services.influencer_marketing.influencer_marketing_service import InfluencerMarketingService
from app.services.cli_tools.cli_agent_service import CLIToolAgentService
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedAIAgentService(IAIAgentService):
    """Enhanced AI Agent Service with real-time data integration"""
    
    def __init__(self):
        self.web_search_factory = WebSearchFactory()
        self.social_media_factory = SocialMediaFactory()
        self.analytics_service = RealTimeAnalyticsService()
        self.influencer_service = InfluencerMarketingService()
        self.cli_agent_service = CLIToolAgentService()
        self.ollama_model = settings.OLLAMA_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        
        # Connection pooling for Ollama client
        self._ollama_client = None
        self._client_lock = threading.Lock()
        
        # Simple in-memory cache
        self._cache = {}
        self._cache_lock = threading.Lock()
    
    def _get_ollama_client(self):
        """Get or create Ollama client with connection pooling"""
        if self._ollama_client is None:
            with self._client_lock:
                if self._ollama_client is None:
                    import ollama
                    self._ollama_client = ollama.Client(host=self.ollama_base_url)
                    logger.info(f"Created new Ollama client connection to {self.ollama_base_url}")
        return self._ollama_client
    
    def _get_cache_key(self, key_type: str, **kwargs) -> str:
        """Generate cache key"""
        return f"{key_type}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
    
    def _get_from_cache(self, cache_key: str, max_age_seconds: int = 300) -> Optional[Any]:
        """Get item from cache if not expired"""
        with self._cache_lock:
            if cache_key in self._cache:
                cached_item = self._cache[cache_key]
                if datetime.now().timestamp() - cached_item['timestamp'] < max_age_seconds:
                    logger.info(f"Cache hit for key: {cache_key}")
                    return cached_item['data']
                else:
                    # Remove expired item
                    del self._cache[cache_key]
                    logger.info(f"Cache expired for key: {cache_key}")
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set item in cache"""
        with self._cache_lock:
            self._cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().timestamp()
            }
            logger.info(f"Cached data for key: {cache_key}")
    
    async def _get_trending_content_with_cache(self, platform: str):
        """Get trending content with caching"""
        cache_key = self._get_cache_key('trending_content', platform=platform)
        cached_data = self._get_from_cache(cache_key, max_age_seconds=600)  # 10 minutes cache
        
        if cached_data is not None:
            return cached_data
        
        # Fetch fresh data
        data = await self.analytics_service.get_trending_content(platform)
        self._set_cache(cache_key, data)
        return data
    
    async def _get_engagement_trends_with_cache(self, user_id: int, days: int = 30):
        """Get engagement trends with caching"""
        cache_key = self._get_cache_key('engagement_trends', user_id=user_id, days=days)
        cached_data = self._get_from_cache(cache_key, max_age_seconds=300)  # 5 minutes cache
        
        if cached_data is not None:
            return cached_data
        
        # Fetch fresh data
        data = await self.analytics_service.get_engagement_trends(user_id, days=days)
        self._set_cache(cache_key, data)
        return data
    
    async def _get_market_rates_with_cache(self, platform: str, content_type: str):
        """Get market rates with caching"""
        cache_key = self._get_cache_key('market_rates', platform=platform, content_type=content_type)
        cached_data = self._get_from_cache(cache_key, max_age_seconds=900)  # 15 minutes cache
        
        if cached_data is not None:
            return cached_data
        
        # Fetch fresh data
        data = await self.analytics_service.get_market_rates(platform, content_type)
        self._set_cache(cache_key, data)
        return data
    
    async def execute_with_real_time_data(
        self, 
        agent_id: int, 
        prompt: str, 
        context: Dict[str, Any],
        real_time_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent task with real-time data"""
        try:
            # Get agent type from context
            agent_type = context.get('agent_type', 'general')
            
            # Enhance prompt with real-time data
            enhanced_prompt = self._enhance_prompt_with_real_time_data(prompt, real_time_data, agent_type)
            
            # Log the actual enhanced prompt that will be sent to AI
            user_id = context.get('user_id', 'unknown')
            logger.info(f"FINAL ENHANCED PROMPT GENERATED for user {user_id} with agent type {agent_type}:")
            logger.info(f"=== ENHANCED PROMPT START ===")
            logger.info(f"{enhanced_prompt}")
            logger.info(f"=== ENHANCED PROMPT END ===")
            
            # Get additional real-time context
            additional_context = await self._gather_additional_context(agent_type, context, real_time_data)
            
            # Execute with Ollama
            response = await self._execute_with_ollama(enhanced_prompt, additional_context, agent_type)
            
            # Format response
            formatted_response = self._format_enhanced_response(
                agent_id=agent_id,
                agent_type=agent_type,
                response=response,
                real_time_data=real_time_data,
                context=context
            )
            
            logger.info(f"Enhanced AI agent {agent_id} executed successfully with real-time data")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Enhanced AI agent execution failed: {e}")
            return self._get_fallback_response(agent_id, agent_type, str(e))
    
    async def get_enhanced_recommendations(
        self, 
        user_id: int, 
        agent_type: str,
        real_time_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get enhanced recommendations with real-time data"""
        try:
            logger.info(f"Starting enhanced recommendations process for user {user_id} with agent type: {agent_type}")
            
            # Gather real-time data based on agent type
            logger.info(f"Phase 1: Gathering real-time data for user {user_id}")
            real_time_data = await self._gather_agent_specific_data(user_id, agent_type, real_time_context)
            logger.info(f"Phase 1 completed: Real-time data gathered for user {user_id}")
            
            # Create base prompt
            logger.info(f"Phase 2: Creating base prompt for user {user_id}")
            base_prompt = self._create_enhanced_prompt(agent_type, real_time_data, real_time_context)
            logger.info(f"Phase 2 completed: Base prompt created for user {user_id}")
            
            # Execute agent with real-time data
            logger.info(f"Phase 3: Executing AI agent with real-time data for user {user_id}")
            result = await self.execute_with_real_time_data(
                agent_id=0,  # Will be set by caller
                prompt=base_prompt,
                context={'agent_type': agent_type, 'user_id': user_id},
                real_time_data=real_time_data
            )
            logger.info(f"Phase 3 completed: AI agent execution finished for user {user_id}")
            
            logger.info(f"Enhanced recommendations process completed successfully for user {user_id}")
            return {
                'agent_type': agent_type,
                'user_id': user_id,
                'recommendations': result,
                'real_time_data_used': real_time_data,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to get enhanced recommendations: {e}")
            return {
                'agent_type': agent_type,
                'user_id': user_id,
                'error': str(e),
                'generated_at': datetime.now()
            }
    
    def _enhance_prompt_with_real_time_data(
        self, 
        prompt: str, 
        real_time_data: Dict[str, Any], 
        agent_type: str
    ) -> str:
        """Enhance prompt with real-time data"""
        
        enhanced_prompt = f"""
{prompt}

REAL-TIME DATA CONTEXT:
"""
        
        # Add trending content data
        if 'trending_content' in real_time_data:
            enhanced_prompt += f"""
TRENDING CONTENT:
{self._format_trending_content(real_time_data['trending_content'])}
"""
        
        # Add market analysis data
        if 'market_analysis' in real_time_data:
            enhanced_prompt += f"""
MARKET ANALYSIS:
{self._format_market_analysis(real_time_data['market_analysis'])}
"""
        
        # Add competitor data
        if 'competitor_analysis' in real_time_data:
            enhanced_prompt += f"""
COMPETITOR ANALYSIS:
{self._format_competitor_analysis(real_time_data['competitor_analysis'])}
"""
        
        # Add engagement trends
        if 'engagement_trends' in real_time_data:
            enhanced_prompt += f"""
ENGAGEMENT TRENDS:
{self._format_engagement_trends(real_time_data['engagement_trends'])}
"""
        
        # Add brand opportunities
        if 'brand_opportunities' in real_time_data:
            enhanced_prompt += f"""
BRAND OPPORTUNITIES:
{self._format_brand_opportunities(real_time_data['brand_opportunities'])}
"""
        
        # Add agent-specific instructions
        enhanced_prompt += f"""

AGENT-SPECIFIC INSTRUCTIONS:
{self._get_agent_specific_instructions(agent_type)}

Use the real-time data above to provide current, actionable recommendations that reflect the latest trends and market conditions.
"""
        
        return enhanced_prompt
    
    async def _gather_additional_context(
        self, 
        agent_type: str, 
        context: Dict[str, Any], 
        real_time_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather additional context for the agent"""
        
        additional_context = {
            'agent_type': agent_type,
            'timestamp': datetime.now().isoformat(),
            'data_freshness': 'real-time'
        }
        
        # Add web search results if needed
        if agent_type in ['content_advisor', 'growth_advisor']:
            try:
                search_service = self.web_search_factory.create_search_service()
                async with search_service:
                    search_results = await search_service.search_trends(
                        f"{agent_type} influencer marketing", 
                        timeframe="7d"
                    )
                    additional_context['web_search_results'] = [
                        {'title': r.title, 'snippet': r.snippet, 'url': r.url} 
                        for r in search_results[:5]
                    ]
            except Exception as e:
                logger.warning(f"Failed to get web search results: {e}")
        
        return additional_context
    
    async def _execute_with_ollama(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        agent_type: str
    ) -> str:
        """Execute with Ollama using enhanced prompt"""
        try:
            import ollama
            
            logger.info(f"AI starting to work on Internet data for agent type: {agent_type}")
            logger.info(f"AI prompt length: {len(prompt)} characters")
            logger.info(f"AI context data types: {list(context.keys())}")
            
            # Build system context
            system_context = self._build_enhanced_system_context(agent_type, context)
            logger.info(f"AI system context built with {len(system_context)} characters")
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ]
            
            logger.info(f"AI calling Ollama with model: {self.ollama_model}")
            # Call Ollama using connection pool
            client = self._get_ollama_client()
            response = client.chat(
                model=self.ollama_model,
                messages=messages,
                options={
                    "temperature": settings.AI_AGENT_TEMPERATURE,
                    "top_p": settings.AI_AGENT_TOP_P,
                    "max_tokens": settings.AI_AGENT_MAX_TOKENS
                }
            )
            
            ai_response = response.get("message", {}).get("content", "")
            logger.info(f"AI completed processing. Response length: {len(ai_response)} characters")
            logger.info(f"AI summary from Internet data: {ai_response[:200]}..." if len(ai_response) > 200 else f"AI summary from Internet data: {ai_response}")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Ollama execution failed: {e}")
            raise
    
    async def _gather_agent_specific_data(
        self, 
        user_id: int, 
        agent_type: str, 
        real_time_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather agent-specific real-time data"""
        
        logger.info(f"Starting to gather Internet data for user {user_id} with agent type: {agent_type}")
        real_time_data = {}
        
        try:
            # Common data for all agents
            logger.info(f"Obtaining live metrics for user {user_id}")
            real_time_data['live_metrics'] = await self.influencer_service.get_live_metrics(user_id)
            logger.info(f"Successfully obtained live metrics for user {user_id}")
            
            # Agent-specific data gathering with parallel execution
            if agent_type == 'growth_advisor':
                logger.info(f"Gathering trending content data for growth_advisor from Instagram, TikTok, and Twitter (parallel)")
                
                # Parallel data fetching for trending content with caching
                platforms = ['instagram', 'tiktok', 'twitter']
                trending_tasks = [self._get_trending_content_with_cache(platform) for platform in platforms]
                trending_results = await asyncio.gather(*trending_tasks, return_exceptions=True)
                
                real_time_data['trending_content'] = []
                for i, (platform, result) in enumerate(zip(platforms, trending_results)):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to get trending content from {platform}: {result}")
                    else:
                        real_time_data['trending_content'].extend(result)
                        logger.info(f"Successfully obtained {len(result)} trending items from {platform}")
                
                # Parallel execution of engagement trends with caching
                logger.info(f"Obtaining engagement trends for user {user_id} (30 days)")
                real_time_data['engagement_trends'] = await self._get_engagement_trends_with_cache(user_id, days=30)
                logger.info(f"Successfully obtained engagement trends for user {user_id}")
            
            elif agent_type == 'content_advisor':
                logger.info(f"Gathering trending content data for content_advisor from Instagram, TikTok, and YouTube (parallel)")
                
                # Parallel data fetching for trending content with caching
                platforms = ['instagram', 'tiktok', 'youtube']
                trending_tasks = [self._get_trending_content_with_cache(platform) for platform in platforms]
                trending_results = await asyncio.gather(*trending_tasks, return_exceptions=True)
                
                real_time_data['trending_content'] = []
                for i, (platform, result) in enumerate(zip(platforms, trending_results)):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to get trending content from {platform}: {result}")
                    else:
                        real_time_data['trending_content'].extend(result)
                        logger.info(f"Successfully obtained {len(result)} trending items from {platform}")
                
                # Parallel execution of content recommendations
                logger.info(f"Obtaining content recommendations for user {user_id} on Instagram")
                real_time_data['content_recommendations'] = await self.influencer_service.get_content_recommendations(
                    user_id, 'instagram'
                )
                logger.info(f"Successfully obtained content recommendations for user {user_id}")
            
            elif agent_type == 'business_advisor':
                logger.info(f"Obtaining brand partnership opportunities for user {user_id}")
                real_time_data['brand_opportunities'] = await self.influencer_service.get_brand_partnership_opportunities(user_id)
                logger.info(f"Successfully obtained brand opportunities for user {user_id}")
                
                logger.info(f"Obtaining market analysis data for Instagram sponsored posts")
                real_time_data['market_analysis'] = await self.analytics_service.get_market_rates('instagram', 'sponsored_post')
                logger.info(f"Successfully obtained market analysis data")
            
            elif agent_type == 'pricing_advisor':
                logger.info(f"Gathering market analysis data for pricing_advisor from Instagram, TikTok, and YouTube (parallel)")
                
                # Parallel data fetching for market rates with caching
                platforms = ['instagram', 'tiktok', 'youtube']
                market_tasks = [self._get_market_rates_with_cache(platform, 'sponsored_post') for platform in platforms]
                market_results = await asyncio.gather(*market_tasks, return_exceptions=True)
                
                real_time_data['market_analysis'] = []
                for i, (platform, result) in enumerate(zip(platforms, market_results)):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to get market rates from {platform}: {result}")
                    else:
                        real_time_data['market_analysis'].extend(result)
                        logger.info(f"Successfully obtained {len(result)} market rate entries from {platform}")
                
                # Parallel execution of pricing recommendations
                logger.info(f"Obtaining pricing recommendations for user {user_id}")
                real_time_data['pricing_recommendations'] = await self.influencer_service.get_pricing_recommendations(user_id)
                logger.info(f"Successfully obtained pricing recommendations for user {user_id}")
            
            elif agent_type == 'analytics_advisor':
                logger.info(f"Obtaining engagement trends for user {user_id} (30 days)")
                real_time_data['engagement_trends'] = await self.analytics_service.get_engagement_trends(user_id, days=30)
                logger.info(f"Successfully obtained engagement trends for user {user_id}")
                
                logger.info(f"Obtaining competitor analysis for user {user_id}")
                real_time_data['competitor_analysis'] = await self.analytics_service.get_competitor_analysis(
                    user_id, ['competitor1', 'competitor2']
                )
                logger.info(f"Successfully obtained competitor analysis for user {user_id}")
            
            elif agent_type == 'collaboration_advisor':
                logger.info(f"Obtaining brand partnership opportunities for user {user_id}")
                real_time_data['brand_opportunities'] = await self.influencer_service.get_brand_partnership_opportunities(user_id)
                logger.info(f"Successfully obtained brand opportunities for user {user_id}")
                
                logger.info(f"Obtaining market insights for influencer marketing")
                real_time_data['market_insights'] = await self.influencer_service.get_market_insights('influencer marketing')
                logger.info(f"Successfully obtained market insights")
            
            elif agent_type == 'platform_advisor':
                logger.info(f"Gathering trending content data for platform_advisor from Instagram, TikTok, YouTube, and Twitter (parallel)")
                
                # Parallel data fetching for trending content with caching
                platforms = ['instagram', 'tiktok', 'youtube', 'twitter']
                trending_tasks = [self._get_trending_content_with_cache(platform) for platform in platforms]
                trending_results = await asyncio.gather(*trending_tasks, return_exceptions=True)
                
                real_time_data['trending_content'] = []
                for i, (platform, result) in enumerate(zip(platforms, trending_results)):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to get trending content from {platform}: {result}")
                    else:
                        real_time_data['trending_content'].extend(result)
                        logger.info(f"Successfully obtained {len(result)} trending items from {platform}")
            
            elif agent_type == 'engagement_advisor':
                logger.info(f"Obtaining engagement trends for user {user_id} (30 days)")
                real_time_data['engagement_trends'] = await self._get_engagement_trends_with_cache(user_id, days=30)
                logger.info(f"Successfully obtained engagement trends for user {user_id}")
                
                logger.info(f"Obtaining trending content from Instagram")
                real_time_data['trending_content'] = await self._get_trending_content_with_cache('instagram')
                logger.info(f"Successfully obtained trending content from Instagram")
            
            elif agent_type == 'optimization_advisor':
                logger.info(f"Obtaining engagement trends for user {user_id} (30 days)")
                real_time_data['engagement_trends'] = await self._get_engagement_trends_with_cache(user_id, days=30)
                logger.info(f"Successfully obtained engagement trends for user {user_id}")
                
                logger.info(f"Obtaining growth strategies for user {user_id}")
                real_time_data['growth_strategies'] = await self.influencer_service.get_growth_strategies(user_id)
                logger.info(f"Successfully obtained growth strategies for user {user_id}")
            
            elif agent_type == 'content_creator':
                logger.info(f"Initializing CLI Tool Agent for content generation")
                # Check CLI tools readiness
                real_time_data['cli_tools_status'] = await self.cli_agent_service.check_readiness()
                logger.info(f"CLI tools readiness checked for user {user_id}")
                
                # Get system status for CLI tools
                real_time_data['system_status'] = await self.cli_agent_service.get_system_status()
                logger.info(f"CLI system status obtained for user {user_id}")
                
                # Get trending content for inspiration
                logger.info(f"Obtaining trending content from Instagram for content inspiration")
                real_time_data['trending_content'] = await self._get_trending_content_with_cache('instagram')
                logger.info(f"Successfully obtained trending content for content inspiration")
            
        except Exception as e:
            logger.warning(f"Failed to gather some real-time data: {e}")
        
        logger.info(f"Completed gathering Internet data for user {user_id} with agent type: {agent_type}. Data types collected: {list(real_time_data.keys())}")
        return real_time_data
    
    def _create_enhanced_prompt(
        self, 
        agent_type: str, 
        real_time_data: Dict[str, Any], 
        real_time_context: Dict[str, Any]
    ) -> str:
        """Create enhanced prompt for agent"""
        
        base_prompts = {
            'growth_advisor': "Provide growth strategies based on current trends and engagement data",
            'content_advisor': "Recommend content strategies based on trending topics and platform insights",
            'business_advisor': "Suggest business development opportunities and monetization strategies",
            'pricing_advisor': "Provide pricing recommendations based on current market rates",
            'analytics_advisor': "Analyze performance metrics and provide optimization recommendations",
            'collaboration_advisor': "Identify brand partnership opportunities and collaboration strategies",
            'platform_advisor': "Recommend platform-specific strategies and optimizations",
            'engagement_advisor': "Suggest engagement optimization strategies and tactics",
            'optimization_advisor': "Provide performance optimization recommendations and strategies",
            'content_creator': "Generate multimedia content including documents, images, videos, and audio using available CLI tools"
        }
        
        return base_prompts.get(agent_type, "Provide comprehensive recommendations based on current data")
    
    def _build_enhanced_system_context(self, agent_type: str, context: Dict[str, Any]) -> str:
        """Build enhanced system context for agent"""
        
        context_parts = [
            "You are an AI agent specialized in influencer marketing with access to real-time data.",
            f"Your specialization: {agent_type}",
            "",
            "REAL-TIME DATA CAPABILITIES:",
            "- Current trending content and hashtags",
            "- Live engagement metrics and trends", 
            "- Market rate analysis and pricing data",
            "- Brand partnership opportunities",
            "- Competitor analysis and benchmarking",
            "- Platform-specific insights and optimizations"
        ]
        
        # Add CLI tools capabilities for content_creator
        if agent_type == 'content_creator':
            context_parts.extend([
                "- Multimedia content generation using CLI tools",
                "- Document generation (Markdown, PDF, LaTeX, Word, PowerPoint, Excel)",
                "- Image generation using Stable Diffusion",
                "- Video creation using FFMPEG and moviepy",
                "- Audio generation using Text-to-Speech engines",
                "- Multi-modal content creation and orchestration"
            ])
        
        context_parts.extend([
            "",
            "RESPONSE REQUIREMENTS:",
            "- Use real-time data to provide current, actionable recommendations",
            "- Include specific metrics, rates, and trending topics",
            "- Provide concrete next steps and implementation guidance",
            "- Reference current market conditions and trends",
            "- Be specific about timing and urgency of recommendations"
        ])
        
        if agent_type == 'content_creator':
            context_parts.extend([
                "- When generating content, specify the format and tools to use",
                "- Provide detailed instructions for content creation",
                "- Consider trending topics for content inspiration",
                "- Suggest multimedia combinations for maximum impact"
            ])
        
        context_parts.extend([
            "",
            "DATA FRESHNESS: All data provided is current and real-time.",
            "Focus on actionable insights that reflect the latest market conditions."
        ])
        
        return "\n".join(context_parts)
    
    def _format_trending_content(self, trending_content: List) -> str:
        """Format trending content for prompt"""
        if not trending_content:
            return "No trending content data available"
        
        formatted = []
        for content in trending_content[:10]:  # Limit to top 10
            formatted.append(f"- {content.hashtag} ({content.platform}): {content.post_count} posts, {content.engagement_rate:.1f}% engagement")
        
        return "\n".join(formatted)
    
    def _format_market_analysis(self, market_analysis: List) -> str:
        """Format market analysis for prompt"""
        if not market_analysis:
            return "No market analysis data available"
        
        formatted = []
        for analysis in market_analysis[:5]:  # Limit to top 5
            rate_range = analysis.rate_range
            formatted.append(f"- {analysis.platform} ({analysis.content_type}): ${rate_range['min']:.0f}-${rate_range['max']:.0f} {rate_range['currency']}")
        
        return "\n".join(formatted)
    
    def _format_competitor_analysis(self, competitor_analysis: List) -> str:
        """Format competitor analysis for prompt"""
        if not competitor_analysis:
            return "No competitor analysis data available"
        
        formatted = []
        for analysis in competitor_analysis[:5]:  # Limit to top 5
            formatted.append(f"- {analysis.competitor_name} ({analysis.platform}): {analysis.followers:,} followers, {analysis.engagement_rate:.1f}% engagement")
        
        return "\n".join(formatted)
    
    def _format_engagement_trends(self, engagement_trends: List) -> str:
        """Format engagement trends for prompt"""
        if not engagement_trends:
            return "No engagement trends data available"
        
        latest = engagement_trends[-1] if engagement_trends else None
        if not latest:
            return "No engagement trends data available"
        
        return f"Current: {latest.followers:,} followers, {latest.engagement_rate:.1f}% engagement rate"
    
    def _format_brand_opportunities(self, brand_opportunities: List) -> str:
        """Format brand opportunities for prompt"""
        if not brand_opportunities:
            return "No brand opportunities data available"
        
        formatted = []
        for opportunity in brand_opportunities[:5]:  # Limit to top 5
            formatted.append(f"- {opportunity['title']}: {opportunity['compensation_range']} (Relevance: {opportunity['relevance_score']:.1f})")
        
        return "\n".join(formatted)
    
    def _get_agent_specific_instructions(self, agent_type: str) -> str:
        """Get agent-specific instructions"""
        
        instructions = {
            'growth_advisor': "Focus on audience growth strategies using trending content and engagement optimization techniques.",
            'content_advisor': "Recommend content strategies based on trending hashtags and platform-specific best practices.",
            'business_advisor': "Identify monetization opportunities and brand partnership strategies based on current market conditions.",
            'pricing_advisor': "Provide pricing recommendations based on current market rates and competitive positioning.",
            'analytics_advisor': "Analyze performance metrics and provide data-driven optimization recommendations.",
            'collaboration_advisor': "Identify brand partnership opportunities and collaboration strategies based on current market trends.",
            'platform_advisor': "Recommend platform-specific strategies and optimizations based on current platform trends.",
            'engagement_advisor': "Suggest engagement optimization strategies based on current engagement trends and best practices.",
            'optimization_advisor': "Provide performance optimization recommendations based on current analytics and market conditions."
        }
        
        return instructions.get(agent_type, "Provide comprehensive recommendations based on current data and trends.")
    
    def _format_enhanced_response(
        self, 
        agent_id: int, 
        agent_type: str, 
        response: str, 
        real_time_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format enhanced response"""
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "focus_area": self._get_focus_area(agent_type),
            "response": response,
            "status": "success",
            "real_time_data_used": {
                "data_types": list(real_time_data.keys()),
                "data_freshness": "real-time",
                "timestamp": datetime.now().isoformat()
            },
            "context_used": {
                "current_prompt": context.get("current_prompt", ""),
                "user_id": context.get("user_id"),
                "agent_id": agent_id,
                "enhancement_level": "real-time"
            }
        }
    
    def _get_focus_area(self, agent_type: str) -> str:
        """Get focus area based on agent type"""
        focus_areas = {
            "growth_advisor": "audience_growth",
            "business_advisor": "business_development",
            "content_advisor": "content_strategy",
            "analytics_advisor": "performance_analysis",
            "collaboration_advisor": "partnership_strategy",
            "pricing_advisor": "pricing_optimization",
            "platform_advisor": "platform_strategy",
            "compliance_advisor": "regulatory_compliance",
            "engagement_advisor": "audience_engagement",
            "optimization_advisor": "performance_optimization"
        }
        
        return focus_areas.get(agent_type, "general_analysis")
    
    def _get_fallback_response(self, agent_id: int, agent_type: str, error: str) -> Dict[str, Any]:
        """Get fallback response when execution fails"""
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "focus_area": self._get_focus_area(agent_type),
            "response": f"Unable to provide real-time recommendations due to: {error}. Please try again later.",
            "status": "error",
            "real_time_data_used": {
                "data_types": [],
                "data_freshness": "none",
                "timestamp": datetime.now().isoformat()
            },
            "context_used": {
                "current_prompt": "Fallback response due to system error",
                "user_id": None,
                "agent_id": agent_id,
                "enhancement_level": "fallback"
            }
        }
