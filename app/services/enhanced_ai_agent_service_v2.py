"""
Enhanced AI Agent Service V2 with Vector Database, MCP Tool Calling, and Smart Context
Following SOLID principles
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.interfaces import IAIAgentService
from app.services.ai_agent_interfaces import IEnhancedAIAgent, IDataRetriever, IContextManager, IToolCaller, IPromptBuilder, IAIExecutor
from app.services.vector_db import VectorDatabaseService
from app.services.mcp_client import MCPClient
from app.services.ai_agent_vector_data_retriever import VectorDataRetriever
from app.services.ai_agent_context_manager import AIAgentContextManager
from app.services.ai_agent_tool_caller import AIAgentToolCaller
from app.services.ai_agent_prompt_builder import AIAgentPromptBuilder
from app.services.ai_agent_executor import AIAgentExecutor
from app.services.web_search.web_search_factory import WebSearchFactory
from app.services.analytics.real_time_analytics import RealTimeAnalyticsService
from app.services.influencer_marketing.influencer_marketing_service import InfluencerMarketingService

logger = logging.getLogger(__name__)


class EnhancedAIAgentServiceV2(IAIAgentService, IEnhancedAIAgent):
    """Enhanced AI Agent Service V2 with Vector Database, MCP Tool Calling, and Smart Context"""
    
    def __init__(self):
        # Initialize core services
        self.vector_db = VectorDatabaseService()
        self.mcp_client = MCPClient()
        
        # Initialize component services following SOLID principles
        self.data_retriever: IDataRetriever = VectorDataRetriever(self.vector_db)
        self.context_manager: IContextManager = AIAgentContextManager(self.vector_db)
        self.tool_caller: IToolCaller = AIAgentToolCaller(self.mcp_client)
        self.prompt_builder: IPromptBuilder = AIAgentPromptBuilder()
        self.ai_executor: IAIExecutor = AIAgentExecutor()
        
        # Initialize legacy services for data gathering
        self.web_search_factory = WebSearchFactory()
        self.analytics_service = RealTimeAnalyticsService()
        self.influencer_service = InfluencerMarketingService()
        
        # Simple in-memory cache
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def process_request(self, user_id: int, agent_type: str, user_query: str) -> Dict[str, Any]:
        """Process user request with enhanced architecture"""
        try:
            logger.info(f"EnhancedAIAgentServiceV2: Processing request for user {user_id} with agent type '{agent_type}'")
            logger.info(f"EnhancedAIAgentServiceV2: User query: {user_query}")
            
            # Phase 1: Gather and store real-time data
            logger.info(f"Phase 1: Gathering and storing real-time data for user {user_id}")
            await self._gather_and_store_real_time_data(user_id, agent_type, user_query)
            
            # Phase 2: Get smart context using vector search
            logger.info(f"Phase 2: Getting smart context for user {user_id}")
            smart_context = await self.context_manager.get_smart_context(user_query, agent_type)
            
            # Phase 3: Get available tools
            logger.info(f"Phase 3: Getting available tools for agent type '{agent_type}'")
            available_tools = await self.tool_caller.get_available_tools(agent_type)
            
            # Phase 4: Build optimized prompt
            logger.info(f"Phase 4: Building optimized prompt for user {user_id}")
            optimized_prompt = self.prompt_builder.build_prompt(user_query, smart_context, agent_type)
            
            # Phase 5: Execute AI with tool calling
            logger.info(f"Phase 5: Executing AI with tool calling for user {user_id}")
            ai_response = await self.ai_executor.execute_with_tools(optimized_prompt, available_tools, agent_type)
            
            # Phase 6: Format response
            logger.info(f"Phase 6: Formatting response for user {user_id}")
            formatted_response = self._format_enhanced_response(
                user_id=user_id,
                agent_type=agent_type,
                response=ai_response,
                context_used=smart_context,
                tools_used=available_tools
            )
            
            logger.info(f"EnhancedAIAgentServiceV2: Successfully processed request for user {user_id}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"EnhancedAIAgentServiceV2: Failed to process request for user {user_id}: {e}")
            return self._get_fallback_response(user_id, agent_type, str(e))
    
    async def get_enhanced_recommendations(
        self, 
        user_id: int, 
        agent_type: str,
        real_time_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get enhanced recommendations with enhanced architecture"""
        try:
            logger.info(f"EnhancedAIAgentServiceV2: Getting enhanced recommendations for user {user_id} with agent type: {agent_type}")
            
            # Extract user query from context
            user_query = real_time_context.get('query', f"Provide recommendations for {agent_type}")
            
            # Process request using enhanced architecture
            result = await self.process_request(user_id, agent_type, user_query)
            
            logger.info(f"EnhancedAIAgentServiceV2: Enhanced recommendations completed for user {user_id}")
            return {
                'agent_type': agent_type,
                'user_id': user_id,
                'recommendations': result,
                'architecture_version': 'v2_enhanced',
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"EnhancedAIAgentServiceV2: Failed to get enhanced recommendations: {e}")
            return {
                'agent_type': agent_type,
                'user_id': user_id,
                'error': str(e),
                'architecture_version': 'v2_enhanced',
                'generated_at': datetime.now()
            }
    
    async def _gather_and_store_real_time_data(self, user_id: int, agent_type: str, user_query: str) -> None:
        """Gather and store real-time data using MCP tools and vector database"""
        try:
            logger.info(f"EnhancedAIAgentServiceV2: Gathering real-time data using MCP tools for user {user_id} with agent type '{agent_type}'")
            
            # Gather data using MCP tools instead of legacy APIs
            data_to_store = []
            
            # Use MCP DuckDuckGo search tools for all data gathering
            try:
                # Search for trends using DuckDuckGo MCP tools
                trends_result = await self.tool_caller.execute_tool_call(
                    "duckduckgo_search_web",
                    {
                        "query": f"{agent_type} influencer marketing trends",
                        "limit": 5
                    }
                )
                
                if "error" not in trends_result:
                    for result in trends_result.get("results", []):
                        data_to_store.append({
                            'title': result.get("title", ""),
                            'content': result.get("snippet", ""),
                            'url': result.get("url", ""),
                            'type': 'trending_topic',
                            'relevance_score': result.get("relevance_score", 0.0)
                        })
                
                # Search for influencers using DuckDuckGo MCP tools
                influencers_result = await self.tool_caller.execute_tool_call(
                    "duckduckgo_search_web",
                    {
                        "query": f"{agent_type} influencers social media",
                        "limit": 3
                    }
                )
                
                if "error" not in influencers_result:
                    for result in influencers_result.get("results", []):
                        data_to_store.append({
                            'title': f"Influencer Data: {result.get('title', '')}",
                            'content': f"{result.get('snippet', '')} - Source: {result.get('source', 'DuckDuckGo')}",
                            'url': result.get('url', ''),
                            'type': 'influencer_data',
                            'relevance_score': result.get('relevance_score', 0.9)
                        })
                
                # Search for content using DuckDuckGo MCP tools
                content_result = await self.tool_caller.execute_tool_call(
                    "duckduckgo_search_web",
                    {
                        "query": f"{agent_type} content strategies social media",
                        "limit": 3
                    }
                )
                
                if "error" not in content_result:
                    for result in content_result.get("results", []):
                        data_to_store.append({
                            'title': f"Content Strategy: {result.get('title', '')}",
                            'content': f"{result.get('snippet', '')} - Source: {result.get('source', 'DuckDuckGo')}",
                            'url': result.get('url', ''),
                            'type': 'content_strategy',
                            'relevance_score': result.get('relevance_score', 0.8)
                        })
                
                # Search for hashtags using DuckDuckGo MCP tools
                hashtags_result = await self.tool_caller.execute_tool_call(
                    "duckduckgo_search_web",
                    {
                        "query": f"{agent_type} hashtags trending social media",
                        "limit": 3
                    }
                )
                
                if "error" not in hashtags_result:
                    for result in hashtags_result.get("results", []):
                        data_to_store.append({
                            'title': f"Hashtag Trends: {result.get('title', '')}",
                            'content': f"{result.get('snippet', '')} - Source: {result.get('source', 'DuckDuckGo')}",
                            'url': result.get('url', ''),
                            'type': 'trending_hashtag',
                            'relevance_score': result.get('relevance_score', 0.85)
                        })
                
                logger.info(f"EnhancedAIAgentServiceV2: Gathered {len(data_to_store)} items using DuckDuckGo MCP tools")
                
            except Exception as e:
                logger.warning(f"EnhancedAIAgentServiceV2: DuckDuckGo MCP tool calls failed: {e}")
                # Fallback to minimal data
                data_to_store.append({
                    'title': f"{agent_type} recommendations",
                    'content': f"Based on current {agent_type} trends and best practices",
                    'type': 'fallback_data',
                    'relevance_score': 0.5
                })
            
            # Store data in vector database
            if data_to_store:
                await self.context_manager.store_context(data_to_store, agent_type)
                logger.info(f"EnhancedAIAgentServiceV2: Stored {len(data_to_store)} data items in vector database using DuckDuckGo MCP tools")
            
        except Exception as e:
            logger.warning(f"EnhancedAIAgentServiceV2: Failed to gather real-time data using DuckDuckGo MCP tools: {e}")
    
    
    def _format_enhanced_response(
        self, 
        user_id: int, 
        agent_type: str, 
        response: str, 
        context_used: str,
        tools_used: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format enhanced response"""
        
        return {
            "user_id": user_id,
            "agent_type": agent_type,
            "focus_area": self._get_focus_area(agent_type),
            "response": response,
            "status": "success",
            "architecture_version": "v2_enhanced",
            "context_used": {
                "smart_context_length": len(context_used),
                "context_preview": context_used[:200] + "..." if len(context_used) > 200 else context_used,
                "data_freshness": "real-time"
            },
            "tools_available": {
                "tool_count": len(tools_used),
                "tools": [tool.get("function", {}).get("name", "unknown") for tool in tools_used]
            },
            "timestamp": datetime.now().isoformat()
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
    
    def _get_fallback_response(self, user_id: int, agent_type: str, error: str) -> Dict[str, Any]:
        """Get fallback response when execution fails"""
        
        return {
            "user_id": user_id,
            "agent_type": agent_type,
            "focus_area": self._get_focus_area(agent_type),
            "response": f"Unable to provide enhanced recommendations due to: {error}. Please try again later.",
            "status": "error",
            "architecture_version": "v2_enhanced",
            "context_used": {
                "smart_context_length": 0,
                "context_preview": "No context available",
                "data_freshness": "none"
            },
            "tools_available": {
                "tool_count": 0,
                "tools": []
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # Legacy method for backward compatibility
    async def execute_with_real_time_data(
        self, 
        agent_id: int, 
        prompt: str, 
        context: Dict[str, Any],
        real_time_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        try:
            user_id = context.get('user_id', 0)
            agent_type = context.get('agent_type', 'general')
            
            # Use enhanced architecture
            result = await self.process_request(user_id, agent_type, prompt)
            
            return {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "response": result.get("response", ""),
                "status": "success",
                "architecture_version": "v2_enhanced"
            }
            
        except Exception as e:
            logger.error(f"Legacy execute_with_real_time_data failed: {e}")
            return {
                "agent_id": agent_id,
                "agent_type": context.get('agent_type', 'general'),
                "response": f"Error: {str(e)}",
                "status": "error",
                "architecture_version": "v2_enhanced"
            }
