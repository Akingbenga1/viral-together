import ollama
import requests
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from app.core.config import settings
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class AIAgentService:
    """Enhanced AI Agent Service with Ollama integration, tool calling, and MCP connectivity"""
    
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        self.mcp_config = settings.get_mcp_config()
        self.tools_enabled = settings.AI_AGENT_TOOL_CALLING_ENABLED
        self.mcp_enabled = settings.AI_AGENT_MCP_ENABLED
        self.mcp_client = MCPClient()
        
    async def execute_agent_task(
        self, 
        agent_id: int, 
        prompt: str, 
        context: Dict[str, Any],
        agent_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Execute agent task with real Ollama integration, tool calling, and MCP connectivity
        Returns response compatible with influencer_recommendations table structure
        """
        try:
            # Build system context for the agent
            system_context = self._build_agent_system_context(agent_type, context)
            
            # Prepare messages for Ollama
            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ]
            
            # Add conversation history if available
            if context.get("conversation_history"):
                for msg in context["conversation_history"][-5:]:  # Limit to last 5 messages
                    messages.insert(-1, {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Prepare Ollama options
            options = {
                "temperature": settings.AI_AGENT_TEMPERATURE,
                "top_p": settings.AI_AGENT_TOP_P,
                "max_tokens": settings.AI_AGENT_MAX_TOKENS,
                "stop": ["<|endoftext|>", "<|im_end|>"]
            }
            
            # Add tools if enabled
            tools = []
            if self.tools_enabled:
                tools = self._get_available_tools(agent_type)
                if tools:
                    options["tools"] = tools
            
            logger.info(f"🤖 AI AGENT: Executing task for agent {agent_id} ({agent_type})")
            logger.info(f"🤖 AI AGENT: Using model {self.model} with {len(tools)} tools")
            print(f"🔍 DEBUG: AI Agent Service - Starting execution for agent {agent_id} ({agent_type})")
            print(f"🔍 DEBUG: AI Agent Service - Model: {self.model}, Tools: {len(tools)}")
            
            # Call Ollama with tool calling support
            if tools:
                print(f"🔍 DEBUG: AI Agent Service - Calling Ollama with tools for agent {agent_id}")
                client = ollama.Client(host=self.base_url)
                response = client.chat(
                    model=self.model,
                    messages=messages,
                    options=options,
                    stream=False
                )
                
                # Handle tool calls if present
                if response.get("message", {}).get("tool_calls"):
                    tool_results = await self._execute_tool_calls(
                        response["message"]["tool_calls"],
                        agent_type
                    )
                    
                    # Add tool results to conversation and get final response
                    messages.append(response["message"])
                    for tool_result in tool_results:
                        messages.append({
                            "role": "tool",
                            "content": tool_result["content"],
                            "tool_call_id": tool_result["tool_call_id"]
                        })
                    
                    # Get final response after tool execution
                    client = ollama.Client(host=self.base_url)
                    final_response = client.chat(
                        model=self.model,
                        messages=messages,
                        options=options,
                        stream=False
                    )
                    
                    response = final_response
            else:
                # Standard response without tool calling
                print(f"🔍 DEBUG: AI Agent Service - Calling Ollama without tools for agent {agent_id}")
                client = ollama.Client(host=self.base_url)
                response = client.chat(
                    model=self.model,
                    messages=messages,
                    options=options,
                    stream=False
                )
            
            # Extract response content
            if response and "message" in response:
                assistant_message = response["message"]["content"]
                
                # Strip thinking/reasoning parts from the response
                cleaned_response = self._strip_thinking_content(assistant_message)
                
                # Format response for influencer recommendations table
                formatted_response = self._format_agent_response(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    response=cleaned_response,
                    context=context
                )
                
                logger.info(f"🤖 AI AGENT: Successfully generated response for agent {agent_id}")
                return formatted_response
            else:
                logger.error("🤖 AI AGENT: Invalid response format from Ollama")
                return self._get_fallback_response(agent_id, agent_type)
                
        except Exception as e:
            logger.error(f"🤖 AI AGENT: Error executing task for agent {agent_id}: {str(e)}")
            return self._get_fallback_response(agent_id, agent_type)
    
    def _build_agent_system_context(self, agent_type: str, context: Dict[str, Any]) -> str:
        """Build system context for the AI agent"""
        
        context_parts = []
        
        # Language enforcement
        context_parts.append("LANGUAGE: ENGLISH ONLY. Respond in English language exclusively.")
        context_parts.append("")
        
        # Agent-specific instructions
        agent_instructions = self._get_agent_instructions(agent_type)
        context_parts.append(f"You are an AI agent specialized in {agent_type} analysis for influencer marketing.")
        context_parts.append(agent_instructions)
        context_parts.append("")
        
        # Response format requirements
        context_parts.append("RESPONSE FORMAT REQUIREMENTS:")
        context_parts.append("- Provide actionable, specific recommendations")
        context_parts.append("- Focus on practical strategies and tactics")
        context_parts.append("- Include specific metrics and goals where relevant")
        context_parts.append("- Structure your response in clear sections")
        context_parts.append("- Be concise but comprehensive")
        context_parts.append("")
        
        # Context information
        if context.get("user_profile"):
            context_parts.append("USER PROFILE CONTEXT:")
            context_parts.append(f"- User ID: {context['user_profile'].get('user_id', 'N/A')}")
            context_parts.append(f"- Username: {context['user_profile'].get('username', 'N/A')}")
            context_parts.append("")
        
        if context.get("analysis_result"):
            context_parts.append("ANALYSIS CONTEXT:")
            context_parts.append(f"- Improvement Areas: {', '.join(context['analysis_result'].get('improvement_areas', []))}")
            context_parts.append(f"- Priorities: {', '.join(context['analysis_result'].get('recommendation_priorities', []))}")
            context_parts.append("")
        
        # Tool usage instructions
        if self.tools_enabled:
            context_parts.append("TOOL USAGE:")
            context_parts.append("- Use available tools to gather current information when needed")
            context_parts.append("- Cite sources and data when using tools")
            context_parts.append("- Focus on actionable insights from tool results")
            context_parts.append("")
        
        context_parts.append("FINAL REMINDER: Respond in ENGLISH ONLY with practical, actionable recommendations.")
        
        return "\n".join(context_parts)
    
    def _get_agent_instructions(self, agent_type: str) -> str:
        """Get agent-specific instructions"""
        
        instructions = {
            "growth_advisor": """
            GROWTH ADVISOR SPECIALIZATION:
            - Focus on audience growth strategies and tactics
            - Provide specific follower growth targets and methods
            - Recommend content strategies for viral potential
            - Suggest collaboration opportunities for growth
            - Include engagement optimization techniques
            """,
            
            "business_advisor": """
            BUSINESS ADVISOR SPECIALIZATION:
            - Focus on monetization and business development
            - Provide pricing strategy recommendations
            - Suggest brand partnership opportunities
            - Recommend business model optimizations
            - Include revenue diversification strategies
            """,
            
            "content_advisor": """
            CONTENT ADVISOR SPECIALIZATION:
            - Focus on content strategy and creation
            - Provide content calendar recommendations
            - Suggest trending content formats
            - Recommend hashtag strategies
            - Include content optimization techniques
            """,
            
            "analytics_advisor": """
            ANALYTICS ADVISOR SPECIALIZATION:
            - Focus on performance metrics and analysis
            - Provide data-driven recommendations
            - Suggest measurement and tracking strategies
            - Recommend optimization based on data
            - Include KPI setting and monitoring
            """,
            
            "collaboration_advisor": """
            COLLABORATION ADVISOR SPECIALIZATION:
            - Focus on brand partnership strategies
            - Provide collaboration opportunity identification
            - Suggest partnership negotiation tactics
            - Recommend cross-promotion strategies
            - Include relationship building techniques
            """,
            
            "pricing_advisor": """
            PRICING ADVISOR SPECIALIZATION:
            - Focus on rate card optimization
            - Provide pricing strategy recommendations
            - Suggest value-based pricing approaches
            - Recommend market rate analysis
            - Include negotiation strategies
            """,
            
            "platform_advisor": """
            PLATFORM ADVISOR SPECIALIZATION:
            - Focus on multi-platform strategies
            - Provide platform-specific recommendations
            - Suggest platform optimization techniques
            - Recommend cross-platform content strategies
            - Include platform algorithm insights
            """,
            
            "compliance_advisor": """
            COMPLIANCE ADVISOR SPECIALIZATION:
            - Focus on legal and regulatory compliance
            - Provide disclosure requirement guidance
            - Suggest best practices for sponsored content
            - Recommend contract negotiation tips
            - Include industry standard compliance
            """,
            
            "engagement_advisor": """
            ENGAGEMENT ADVISOR SPECIALIZATION:
            - Focus on audience engagement strategies
            - Provide interaction optimization techniques
            - Suggest community building approaches
            - Recommend engagement metric improvements
            - Include audience retention strategies
            """,
            
            "optimization_advisor": """
            OPTIMIZATION ADVISOR SPECIALIZATION:
            - Focus on performance optimization
            - Provide efficiency improvement strategies
            - Suggest workflow optimizations
            - Recommend productivity enhancements
            - Include automation opportunities
            """
        }
        
        return instructions.get(agent_type, """
        GENERAL ADVISOR SPECIALIZATION:
        - Provide comprehensive influencer marketing guidance
        - Focus on overall strategy and best practices
        - Include practical implementation tips
        - Recommend industry best practices
        - Provide balanced, well-rounded advice
        """)
    
    def _get_available_tools(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get available tools for the agent"""
        
        tools = []
        
        # Web search tool
        if settings.WEB_SEARCH_ENABLED:
            tools.append({
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information about influencer marketing, social media trends, or industry data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for web search"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            })
        
        # MCP tools if enabled - but only if MCP is actually working
        if self.mcp_enabled:
            try:
                mcp_tools = self.mcp_client.get_tools_for_agent(agent_type)
                if mcp_tools:
                    tools.extend(mcp_tools)
                    print(f"🔍 DEBUG: Added {len(mcp_tools)} MCP tools for agent {agent_type}")
                else:
                    print(f"🔍 DEBUG: No MCP tools available for agent {agent_type}")
            except Exception as e:
                print(f"🔍 DEBUG: MCP tools disabled due to error: {str(e)}")
                # Continue without MCP tools - don't let MCP failure break Ollama
        
        return tools
    
    async def _execute_tool_calls(self, tool_calls: List[Dict], agent_type: str) -> List[Dict]:
        """Execute tool calls and return results"""
        
        results = []
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                if tool_name == "web_search":
                    result = await self._execute_web_search(tool_args)
                elif tool_name.startswith("search_twitter"):
                    result = await self.mcp_client.call_mcp_server("twitter-tools", tool_name, tool_args)
                elif tool_name.startswith("get_youtube"):
                    result = await self.mcp_client.call_mcp_server("youtube-tools", tool_name, tool_args)
                elif tool_name.startswith("get_instagram"):
                    result = await self.mcp_client.call_mcp_server("instagram-tools", tool_name, tool_args)
                elif tool_name.startswith("get_facebook"):
                    result = await self.mcp_client.call_mcp_server("facebook-tools", tool_name, tool_args)
                elif tool_name.startswith("get_linkedin"):
                    result = await self.mcp_client.call_mcp_server("linkedin-tools", tool_name, tool_args)
                elif tool_name.startswith("get_tiktok"):
                    result = await self.mcp_client.call_mcp_server("tiktok-tools", tool_name, tool_args)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                results.append({
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })
                
            except Exception as e:
                logger.error(f"🤖 AI AGENT: Error executing tool call: {str(e)}")
                results.append({
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps({"error": str(e)})
                })
        
        return results
    
    async def _execute_web_search(self, args: Dict) -> Dict:
        """Execute web search"""
        
        try:
            query = args.get("query", "")
            max_results = args.get("max_results", 5)
            
            # Simple web search implementation (you can enhance this)
            # For now, return a structured response
            return {
                "query": query,
                "results": [
                    {
                        "title": f"Search result for: {query}",
                        "snippet": f"Information about {query} relevant to influencer marketing",
                        "url": f"https://example.com/search?q={query}"
                    }
                ],
                "total_results": max_results
            }
            
        except Exception as e:
            return {"error": f"Web search failed: {str(e)}"}
    
    def _format_agent_response(
        self, 
        agent_id: int, 
        agent_type: str, 
        response: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format agent response for influencer recommendations table"""
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "focus_area": self._get_focus_area(agent_type),
            "response": response,
            "status": "success",
            "context_used": {
                "current_prompt": context.get("current_prompt", ""),
                "conversation_history": context.get("conversation_history", []),
                "agent_responses": context.get("agent_responses", []),
                "context_metadata": {
                    "user_id": context.get("user_id"),
                    "agent_id": agent_id,
                    "context_window": context.get("context_window", 10)
                }
            }
        }
    
    def _strip_thinking_content(self, response: str) -> str:
        """Strip thinking/reasoning content from Ollama response"""
        
        if not response:
            return response
        
        # Common thinking patterns to remove
        thinking_patterns = [
            r'<thinking>.*?</thinking>',
            r'<reasoning>.*?</reasoning>',
            r'<analysis>.*?</analysis>',
            r'<thought>.*?</thought>',
            r'<step>.*?</step>',
            r'<process>.*?</process>',
            r'Let me think about this.*?',
            r'Let me analyze.*?',
            r'First, let me.*?',
            r'To answer this.*?',
            r'Based on my analysis.*?',
            r'After considering.*?',
            r'Now, let me provide.*?',
            r'Here\'s my thinking.*?',
            r'Let me break this down.*?',
            r'To provide the best answer.*?',
            r'Let me approach this.*?',
            r'In order to.*?',
            r'Let me start by.*?',
            r'Let me begin by.*?',
            r'Let me first.*?',
            r'Let me consider.*?',
            r'Let me examine.*?',
            r'Let me look at.*?',
            r'Let me review.*?',
            r'Let me check.*?',
            r'Let me verify.*?',
            r'Let me confirm.*?',
            r'Let me understand.*?',
            r'Let me clarify.*?',
            r'Let me explain.*?',
            r'Let me describe.*?',
            r'Let me outline.*?',
            r'Let me summarize.*?',
            r'Let me conclude.*?',
            r'Let me finish.*?',
            r'Let me end.*?',
            r'Let me wrap up.*?',
            r'Let me close.*?',
            r'Let me finalize.*?',
            r'Let me complete.*?',
            r'Let me finish up.*?',
            r'Let me wrap this up.*?',
            r'Let me close this.*?',
            r'Let me end this.*?',
            r'Let me conclude this.*?',
            r'Let me summarize this.*?',
            r'Let me outline this.*?',
            r'Let me describe this.*?',
            r'Let me explain this.*?',
            r'Let me clarify this.*?',
            r'Let me understand this.*?',
            r'Let me confirm this.*?',
            r'Let me verify this.*?',
            r'Let me check this.*?',
            r'Let me review this.*?',
            r'Let me look at this.*?',
            r'Let me examine this.*?',
            r'Let me consider this.*?',
            r'Let me first.*?',
            r'Let me begin by.*?',
            r'Let me start by.*?',
            r'In order to.*?',
            r'To provide the best answer.*?',
            r'Let me approach this.*?',
            r'Let me break this down.*?',
            r'Here\'s my thinking.*?',
            r'Now, let me provide.*?',
            r'After considering.*?',
            r'Based on my analysis.*?',
            r'To answer this.*?',
            r'First, let me.*?',
            r'Let me analyze.*?',
            r'Let me think about this.*?',
            r'<process>.*?</process>',
            r'<step>.*?</step>',
            r'<thought>.*?</thought>',
            r'<analysis>.*?</analysis>',
            r'<reasoning>.*?</reasoning>',
            r'<thinking>.*?</thinking>'
        ]
        
        import re
        
        # Remove thinking patterns
        cleaned_response = response
        for pattern in thinking_patterns:
            cleaned_response = re.sub(pattern, '', cleaned_response, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove extra whitespace and normalize
        cleaned_response = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_response)  # Remove excessive line breaks
        cleaned_response = re.sub(r'^\s+', '', cleaned_response)  # Remove leading whitespace
        cleaned_response = re.sub(r'\s+$', '', cleaned_response)  # Remove trailing whitespace
        
        return cleaned_response.strip()
    
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
    
    def _get_fallback_response(self, agent_id: int, agent_type: str) -> Dict[str, Any]:
        """Get fallback response when Ollama fails"""
        
        fallback_responses = {
            "growth_advisor": """
            GROWTH ADVISOR RECOMMENDATIONS:
            
            1. AUDIENCE GROWTH STRATEGY:
            - Focus on high-engagement content types (polls, questions, behind-the-scenes)
            - Implement consistent posting schedule (5-6 posts per week)
            - Use trending hashtags strategically
            
            2. ENGAGEMENT OPTIMIZATION:
            - Respond to comments within 2 hours
            - Create interactive stories and polls
            - Host weekly Q&A sessions
            
            3. GROWTH TACTICS:
            - Collaborate with complementary influencers
            - Cross-promote on multiple platforms
            - Use user-generated content campaigns
            """,
            
            "business_advisor": """
            BUSINESS ADVISOR RECOMMENDATIONS:
            
            1. MONETIZATION STRATEGY:
            - Develop multiple revenue streams (sponsored posts, affiliate marketing, products)
            - Set competitive but profitable pricing
            - Create value-based service packages
            
            2. BRAND PARTNERSHIPS:
            - Build authentic relationships with brands
            - Focus on long-term partnerships over one-off campaigns
            - Demonstrate ROI to potential partners
            
            3. BUSINESS DEVELOPMENT:
            - Diversify income sources
            - Invest in professional development
            - Build a strong personal brand
            """,
            
            "content_advisor": """
            CONTENT ADVISOR RECOMMENDATIONS:
            
            1. CONTENT STRATEGY:
            - Create a content calendar with themes
            - Mix educational, entertaining, and promotional content
            - Maintain consistent visual style and voice
            
            2. CONTENT OPTIMIZATION:
            - Use trending formats (Reels, Stories, TikTok)
            - Optimize for platform algorithms
            - Include call-to-actions in every post
            
            3. CONTENT PLANNING:
            - Batch create content weekly
            - Plan ahead for seasonal content
            - Repurpose content across platforms
            """
        }
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "focus_area": self._get_focus_area(agent_type),
            "response": fallback_responses.get(agent_type, """
            GENERAL ASSISTANT RECOMMENDATIONS:
            
            1. OVERALL STRATEGY:
            - Develop a unique personal brand
            - Focus on authentic, valuable content
            - Build genuine relationships with audience
            
            2. CONTENT PLANNING:
            - Create content calendar with themes
            - Mix educational, entertaining, and promotional content
            - Maintain consistent visual style
            
            3. SUCCESS METRICS:
            - Track engagement rate improvements
            - Monitor follower quality (not just quantity)
            - Measure brand partnership inquiries
            """),
            "status": "fallback",
            "context_used": {
                "current_prompt": "Fallback response due to system error",
                "conversation_history": [],
                "agent_responses": [],
                "context_metadata": {
                    "user_id": None,
                    "agent_id": agent_id,
                    "context_window": 0
                }
            }
        }
