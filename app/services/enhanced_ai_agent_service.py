"""
Enhanced AI Agent Service with real-time data integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.interfaces import IAIAgentService
from app.services.web_search.web_search_factory import WebSearchFactory
from app.services.social_media.social_media_factory import SocialMediaFactory
from app.services.analytics.real_time_analytics import RealTimeAnalyticsService
from app.services.influencer_marketing.influencer_marketing_service import InfluencerMarketingService
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedAIAgentService(IAIAgentService):
    """Enhanced AI Agent Service with real-time data integration"""
    
    def __init__(self):
        self.web_search_factory = WebSearchFactory()
        self.social_media_factory = SocialMediaFactory()
        self.analytics_service = RealTimeAnalyticsService()
        self.influencer_service = InfluencerMarketingService()
        self.ollama_model = settings.OLLAMA_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL
    
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
            # Gather real-time data based on agent type
            real_time_data = await self._gather_agent_specific_data(user_id, agent_type, real_time_context)
            
            # Create enhanced prompt
            enhanced_prompt = self._create_enhanced_prompt(agent_type, real_time_data, real_time_context)
            
            # Execute agent with real-time data
            result = await self.execute_with_real_time_data(
                agent_id=0,  # Will be set by caller
                prompt=enhanced_prompt,
                context={'agent_type': agent_type, 'user_id': user_id},
                real_time_data=real_time_data
            )
            
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
            
            # Build system context
            system_context = self._build_enhanced_system_context(agent_type, context)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ]
            
            # Call Ollama
            client = ollama.Client(host=self.ollama_base_url)
            response = client.chat(
                model=self.ollama_model,
                messages=messages,
                options={
                    "temperature": settings.AI_AGENT_TEMPERATURE,
                    "top_p": settings.AI_AGENT_TOP_P,
                    "max_tokens": settings.AI_AGENT_MAX_TOKENS
                }
            )
            
            return response.get("message", {}).get("content", "")
            
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
        
        real_time_data = {}
        
        try:
            # Common data for all agents
            real_time_data['live_metrics'] = await self.influencer_service.get_live_metrics(user_id)
            
            # Agent-specific data gathering
            if agent_type == 'growth_advisor':
                real_time_data['trending_content'] = []
                for platform in ['instagram', 'tiktok', 'twitter']:
                    trending = await self.analytics_service.get_trending_content(platform)
                    real_time_data['trending_content'].extend(trending)
                
                real_time_data['engagement_trends'] = await self.analytics_service.get_engagement_trends(user_id, days=30)
            
            elif agent_type == 'content_advisor':
                real_time_data['trending_content'] = []
                for platform in ['instagram', 'tiktok', 'youtube']:
                    trending = await self.analytics_service.get_trending_content(platform)
                    real_time_data['trending_content'].extend(trending)
                
                real_time_data['content_recommendations'] = await self.influencer_service.get_content_recommendations(
                    user_id, 'instagram'
                )
            
            elif agent_type == 'business_advisor':
                real_time_data['brand_opportunities'] = await self.influencer_service.get_brand_partnership_opportunities(user_id)
                real_time_data['market_analysis'] = await self.analytics_service.get_market_rates('instagram', 'sponsored_post')
            
            elif agent_type == 'pricing_advisor':
                real_time_data['market_analysis'] = []
                for platform in ['instagram', 'tiktok', 'youtube']:
                    rates = await self.analytics_service.get_market_rates(platform, 'sponsored_post')
                    real_time_data['market_analysis'].extend(rates)
                
                real_time_data['pricing_recommendations'] = await self.influencer_service.get_pricing_recommendations(user_id)
            
            elif agent_type == 'analytics_advisor':
                real_time_data['engagement_trends'] = await self.analytics_service.get_engagement_trends(user_id, days=30)
                real_time_data['competitor_analysis'] = await self.analytics_service.get_competitor_analysis(
                    user_id, ['competitor1', 'competitor2']
                )
            
            elif agent_type == 'collaboration_advisor':
                real_time_data['brand_opportunities'] = await self.influencer_service.get_brand_partnership_opportunities(user_id)
                real_time_data['market_insights'] = await self.influencer_service.get_market_insights('influencer marketing')
            
            elif agent_type == 'platform_advisor':
                real_time_data['trending_content'] = []
                for platform in ['instagram', 'tiktok', 'youtube', 'twitter']:
                    trending = await self.analytics_service.get_trending_content(platform)
                    real_time_data['trending_content'].extend(trending)
            
            elif agent_type == 'engagement_advisor':
                real_time_data['engagement_trends'] = await self.analytics_service.get_engagement_trends(user_id, days=30)
                real_time_data['trending_content'] = await self.analytics_service.get_trending_content('instagram')
            
            elif agent_type == 'optimization_advisor':
                real_time_data['engagement_trends'] = await self.analytics_service.get_engagement_trends(user_id, days=30)
                real_time_data['growth_strategies'] = await self.influencer_service.get_growth_strategies(user_id)
            
        except Exception as e:
            logger.warning(f"Failed to gather some real-time data: {e}")
        
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
            'optimization_advisor': "Provide performance optimization recommendations and strategies"
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
            "- Platform-specific insights and optimizations",
            "",
            "RESPONSE REQUIREMENTS:",
            "- Use real-time data to provide current, actionable recommendations",
            "- Include specific metrics, rates, and trending topics",
            "- Provide concrete next steps and implementation guidance",
            "- Reference current market conditions and trends",
            "- Be specific about timing and urgency of recommendations",
            "",
            "DATA FRESHNESS: All data provided is current and real-time.",
            "Focus on actionable insights that reflect the latest market conditions."
        ]
        
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
