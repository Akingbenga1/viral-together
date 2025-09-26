"""
AI Agent Prompt Builder following SOLID principles
"""

import logging
from typing import Dict, Any, List
from app.services.ai_agent_interfaces import IPromptBuilder

logger = logging.getLogger(__name__)


class AIAgentPromptBuilder(IPromptBuilder):
    """AI Agent prompt builder implementation"""
    
    def __init__(self):
        self.agent_instructions = {
            'growth_advisor': "Analyze trending content and engagement data to provide specific growth strategies. Reference actual influencers from search results, their follower growth rates, engagement metrics, and provide specific growth targets with timelines. Include exact numbers: follower counts, engagement rates, growth percentages, and revenue projections.",
            'content_advisor': "Examine trending hashtags and platform data to recommend specific content strategies. Reference actual influencers from search results, their content performance metrics, posting schedules, and provide specific content calendars with expected engagement rates and follower growth projections.",
            'business_advisor': "Analyze market conditions and brand opportunities to suggest specific monetization strategies. Reference actual influencers from search results, their earnings, brand partnerships, and provide specific revenue projections, partnership values, and market rates with concrete financial targets.",
            'pricing_advisor': "Examine current market rates and competitive data to provide specific pricing recommendations. Reference actual influencer rates from search results, include specific dollar amounts, rate ranges, and provide concrete pricing strategies with financial justifications and market positioning.",
            'analytics_advisor': "Analyze performance metrics to provide specific optimization recommendations with measurable outcomes. Reference actual influencer performance data from search results, include specific metrics, percentages, and provide concrete improvement targets with timelines and expected ROI.",
            'collaboration_advisor': "Identify specific brand partnership opportunities based on current market trends and influencer data. Reference actual influencers from search results, their collaboration history, and provide specific partnership values, collaboration rates, and revenue projections with concrete financial impact.",
            'platform_advisor': "Recommend platform-specific strategies based on current platform trends and influencer performance. Reference specific influencers from search results, their platform-specific metrics, and provide concrete optimization strategies with measurable outcomes and expected performance improvements.",
            'engagement_advisor': "Analyze current engagement trends to suggest specific optimization strategies with measurable results. Reference actual influencer engagement data from search results, include specific engagement rates, and provide concrete improvement tactics with expected outcomes and performance metrics.",
            'optimization_advisor': "Examine current analytics and market conditions to provide specific performance optimization recommendations. Reference actual influencer performance data from search results, include specific metrics and provide concrete optimization targets with financial impact projections and measurable ROI."
        }
    
    def build_prompt(self, user_query: str, context: str, agent_type: str) -> str:
        """Build optimized prompt with context"""
        try:
            logger.info(f"AIAgentPromptBuilder: Building prompt for agent type '{agent_type}' with context length: {len(context)}")
            
            # Get agent-specific instructions
            agent_instructions = self.agent_instructions.get(agent_type, "Provide comprehensive recommendations based on current data and trends.")
            
            # Build optimized prompt with tool calling emphasis
            prompt = f"""
USER QUERY: {user_query}

RELEVANT CONTEXT:
{context}

AGENT-SPECIFIC INSTRUCTIONS:
{agent_instructions}

TOOL CALLING REQUIREMENTS:
- ALWAYS call relevant tools to get the most current data before responding
- Use search_trends to get trending topics and hashtags
- Use search_influencers to get influencer data and metrics
- Use search_content to get content strategies and examples
- Use search_hashtags to get trending hashtags and engagement data
- Call tools to get real-time data for your recommendations

CRITICAL RESPONSE REQUIREMENTS:
- ALWAYS call tools to get current data before making recommendations
- NEVER use generic phrases like "OK, let's dive deep", "Let me help you", or ask questions at the end
- ALWAYS reference specific influencers mentioned in tool results by name
- Include exact follower counts, engagement rates, and financial metrics from tool data
- Provide specific dollar amounts, percentages, and concrete numbers from tool results
- Reference actual influencer earnings, brand partnership values, and market rates from tools
- Mention specific influencers' content performance, posting schedules, and strategies from tools
- Include specific revenue projections, partnership values, and financial impact from tools
- Provide concrete timelines, deadlines, and measurable outcomes based on tool data
- Use real-time tool data to justify every recommendation with specific evidence

RESPONSE FORMAT REQUIREMENTS:
- Start directly with specific recommendations and data points from tools
- Reference influencers by name: "Based on [Influencer Name]'s success with..."
- Include specific metrics: "With 2.3M followers and 8.5% engagement rate..."
- Provide financial specifics: "Partnership rates range from $5,000-$15,000 per post..."
- End with concrete action steps and expected outcomes based on tool data
- NO generic introductions or conclusions
- NO questions at the end of responses

Use the relevant context above and call tools to get current data to provide actionable recommendations that reflect the latest trends and market conditions with specific influencer examples and concrete financial metrics.
"""
            
            logger.info(f"AIAgentPromptBuilder: Built prompt with {len(prompt)} characters")
            return prompt
            
        except Exception as e:
            logger.error(f"AIAgentPromptBuilder: Failed to build prompt: {e}")
            return user_query
