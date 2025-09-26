"""
AI Agent Tool Caller following SOLID principles
"""

import logging
from typing import Dict, Any, List
from app.services.ai_agent_interfaces import IToolCaller
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class AIAgentToolCaller(IToolCaller):
    """AI Agent tool caller implementation"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
    
    async def get_available_tools(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get available tools for agent type"""
        try:
            logger.info(f"AIAgentToolCaller: Getting available tools for agent type '{agent_type}'")
            
            # Get tools from MCP client
            tools = self.mcp_client.get_tools_for_agent(agent_type)
            
            logger.info(f"AIAgentToolCaller: Found {len(tools)} available tools")
            return tools
            
        except Exception as e:
            logger.error(f"AIAgentToolCaller: Failed to get available tools: {e}")
            return []
    
    async def execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        try:
            logger.info(f"AIAgentToolCaller: Executing tool '{tool_name}' with parameters: {parameters}")
            
            # Determine which MCP server to use based on tool name
            server_name = self._get_server_for_tool(tool_name)
            
            # Execute tool via MCP client
            result = await self.mcp_client.call_mcp_server(
                server_name=server_name,
                tool_name=tool_name,
                parameters=parameters
            )
            
            logger.info(f"AIAgentToolCaller: Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"AIAgentToolCaller: Failed to execute tool '{tool_name}': {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _get_server_for_tool(self, tool_name: str) -> str:
        """Get MCP server name for tool"""
        tool_server_mapping = {
            # DuckDuckGo tools (priority)
            "duckduckgo_search_web": "duckduckgo-search",
            "duckduckgo_get_instant_answer": "duckduckgo-search",
            "duckduckgo_search_news": "duckduckgo-search",
            "duckduckgo_search_images": "duckduckgo-search",
            "duckduckgo_search_videos": "duckduckgo-search",
            # Web search tools (fallback)
            "search_trends": "web-search-tools",
            "search_influencers": "web-search-tools",
            "search_content": "web-search-tools",
            "search_hashtags": "web-search-tools",
            "search_web": "web-search-tools",
            # Social media tools
            "search_twitter_trends": "twitter-tools",
            "get_instagram_insights": "instagram-tools",
            "get_youtube_analytics": "youtube-tools",
            "get_tiktok_analytics": "tiktok-tools",
            "get_facebook_insights": "facebook-tools",
            "get_linkedin_analytics": "linkedin-tools"
        }
        
        return tool_server_mapping.get(tool_name, "duckduckgo-search")
