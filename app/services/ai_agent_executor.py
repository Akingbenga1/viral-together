"""
AI Agent Executor following SOLID principles
"""

import logging
import threading
from typing import Dict, Any, List
from app.services.ai_agent_interfaces import IAIExecutor
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIAgentExecutor(IAIExecutor):
    """AI Agent executor implementation"""
    
    def __init__(self):
        self.ollama_model = settings.OLLAMA_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        
        # Connection pooling for Ollama client
        self._ollama_client = None
        self._client_lock = threading.Lock()
    
    def _get_ollama_client(self):
        """Get or create Ollama client with connection pooling"""
        if self._ollama_client is None:
            with self._client_lock:
                if self._ollama_client is None:
                    import ollama
                    self._ollama_client = ollama.Client(host=self.ollama_base_url)
                    logger.info(f"Created new Ollama client connection to {self.ollama_base_url}")
        return self._ollama_client
    
    async def execute_with_tools(self, prompt: str, tools: List[Dict[str, Any]], agent_type: str) -> str:
        """Execute AI with tool calling support"""
        try:
            logger.info(f"AIAgentExecutor: Executing AI with {len(tools)} tools for agent type '{agent_type}'")
            logger.info(f"AIAgentExecutor: Prompt length: {len(prompt)} characters")
            
            # Build system context with tool information
            system_context = self._build_system_context_with_tools(agent_type, tools)
            logger.info(f"AIAgentExecutor: System context built with {len(system_context)} characters")
            
            # Prepare messages with tool calling support
            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ]
            
            # Add tools to the request if available
            request_options = {
                "temperature": settings.AI_AGENT_TEMPERATURE,
                "top_p": settings.AI_AGENT_TOP_P,
                "max_tokens": settings.AI_AGENT_MAX_TOKENS
            }
            
            # Add tools if available
            if tools:
                request_options["tools"] = tools
                logger.info(f"AIAgentExecutor: Added {len(tools)} tools to request")
            
            logger.info(f"AIAgentExecutor: Calling Ollama with model: {self.ollama_model}")
            
            # Call Ollama using connection pool
            client = self._get_ollama_client()
            response = client.chat(
                model=self.ollama_model,
                messages=messages,
                options=request_options
            )
            
            ai_response = response.get("message", {}).get("content", "")
            logger.info(f"AIAgentExecutor: AI completed processing. Response length: {len(ai_response)} characters")
            logger.info(f"AIAgentExecutor: AI summary: {ai_response[:200]}..." if len(ai_response) > 200 else f"AIAgentExecutor: AI summary: {ai_response}")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"AIAgentExecutor: Ollama execution failed: {e}")
            raise
    
    def _build_system_context_with_tools(self, agent_type: str, tools: List[Dict[str, Any]]) -> str:
        """Build system context with tool information"""
        
        context_parts = [
            "You are an AI agent specialized in influencer marketing with access to real-time data and tools.",
            f"Your specialization: {agent_type}",
            "",
            "AVAILABLE TOOLS:",
        ]
        
        # Add tool information
        for tool in tools:
            tool_name = tool.get("function", {}).get("name", "unknown")
            tool_description = tool.get("function", {}).get("description", "No description")
            context_parts.append(f"- {tool_name}: {tool_description}")
        
        context_parts.extend([
            "",
            "TOOL CALLING INSTRUCTIONS:",
            "- You can call tools to get real-time data when needed",
            "- Use search_trends for trending topics and hashtags",
            "- Use search_influencers for influencer data and metrics",
            "- Use search_content for content strategies and examples",
            "- Use search_hashtags for trending hashtags and engagement data",
            "- Always call tools to get the most current data before making recommendations",
            "",
            "REAL-TIME DATA CAPABILITIES:",
            "- Current trending content and hashtags via tool calls",
            "- Live engagement metrics and trends via tool calls", 
            "- Market rate analysis and pricing data via tool calls",
            "- Brand partnership opportunities via tool calls",
            "- Competitor analysis and benchmarking via tool calls",
            "- Platform-specific insights and optimizations via tool calls",
            "- Web search results with specific influencer mentions via tool calls",
            "",
            "CRITICAL RESPONSE REQUIREMENTS:",
            "- ALWAYS call relevant tools to get current data before responding",
            "- NEVER use generic phrases like 'OK, let's dive deep', 'Let me help you', or ask questions at the end",
            "- ALWAYS reference specific influencers mentioned in tool results by name",
            "- Include exact follower counts, engagement rates, and financial metrics from tool data",
            "- Provide specific dollar amounts, percentages, and concrete numbers from tool results",
            "- Reference actual influencer earnings, brand partnership values, and market rates from tools",
            "- Mention specific influencers' content performance, posting schedules, and strategies from tools",
            "- Include specific revenue projections, partnership values, and financial impact from tools",
            "- Provide concrete timelines, deadlines, and measurable outcomes based on tool data",
            "- Use real-time tool data to justify every recommendation with specific evidence",
            "",
            "DATA-DRIVEN RESPONSE FORMAT:",
            "- Start directly with specific recommendations and data points from tools",
            "- Reference influencers by name: 'Based on [Influencer Name]'s success with...'",
            "- Include specific metrics: 'With 2.3M followers and 8.5% engagement rate...'",
            "- Provide financial specifics: 'Partnership rates range from $5,000-$15,000 per post...'",
            "- End with concrete action steps and expected outcomes based on tool data",
            "",
            "DATA FRESHNESS: All data comes from real-time tool calls.",
            "Focus on actionable insights that reflect the latest market conditions with specific influencer examples from tool results."
        ])
        
        return "\n".join(context_parts)
