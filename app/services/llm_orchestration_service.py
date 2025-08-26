import ollama
import json
import logging
import re
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.db.models.ai_agent import AIAgent

logger = logging.getLogger(__name__)

class LLMOrchestrationService:
    """LLM-based agent orchestration service for intelligent agent selection"""

    def __init__(self):
        self.model = settings.AI_AGENT_ORCHESTRATION_MODEL
        self.base_url = settings.OLLAMA_BASE_URL

    def _parse_json_from_markdown(self, content: str) -> Any:
        """Robust JSON extraction from markdown-wrapped responses"""
        try:
            logger.info(f"🤖 LLM ORCHESTRATION: Starting JSON parsing for content length: {len(content)}")
            logger.info(f"🤖 LLM ORCHESTRATION: Content preview: {repr(content[:300])}")

            # Handle escaped newlines if present
            if "\\n" in content:
                content = content.replace("\\n", "\n")
                logger.info(f"🤖 LLM ORCHESTRATION: Unescaped newlines in content")

            # First, try regex pattern to match content within triple backticks
            pattern = r"```(?:json)?\n(.*?)\n```"
            match = re.search(pattern, content, re.DOTALL)

            if match:
                json_content = match.group(1).strip()
                logger.info(f"🤖 LLM ORCHESTRATION: Extracted JSON using regex: {json_content[:200]}...")
                return json.loads(json_content)

            # If regex fails, try manual extraction
            if "```json" in content and "```" in content:
                start_marker = "```json"
                end_marker = "```"
                start_idx = content.find(start_marker) + len(start_marker)
                end_idx = content.rfind(end_marker)

                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                    json_str = content[start_idx:end_idx].strip()
                    logger.info(f"🤖 LLM ORCHESTRATION: Extracted JSON manually: {json_str[:200]}...")
                    return json.loads(json_str)

            # Try to find JSON array directly
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                logger.info(f"🤖 LLM ORCHESTRATION: Found JSON array: {json_str[:200]}...")
                return json.loads(json_str)

            # Try to find JSON object directly
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                logger.info(f"🤖 LLM ORCHESTRATION: Found JSON object: {json_str[:200]}...")
                return json.loads(json_str)

            # Last resort: try to parse the entire response
            logger.info(f"🤖 LLM ORCHESTRATION: Attempting to parse entire response as JSON")
            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"🤖 LLM ORCHESTRATION: JSON decode error in _parse_json_from_markdown: {str(e)}")
            logger.error(f"🤖 LLM ORCHESTRATION: Failed content: {repr(content)}")
            raise
        except Exception as e:
            logger.error(f"🤖 LLM ORCHESTRATION: Error in _parse_json_from_markdown: {str(e)}")
            logger.error(f"🤖 LLM ORCHESTRATION: Exception type: {type(e).__name__}")
            raise

    async def analyze_task_complexity(self, task_description: str, user_context: Dict[str, Any]) -> str:
        """Analyze task complexity using LLM"""
        try:
            # Enhanced prompt with scope-aware complexity analysis
            prompt = f"""
Analyze the complexity of this task and classify it as simple, medium, or complex.

TASK: {task_description}

ANALYSIS GUIDELINES:
1. **Scope Indicators**: Look for words like "only", "just", "specifically", "focused" - these suggest SIMPLE complexity
2. **Task Count**: Count the number of distinct tasks/strategies mentioned
   - 1-2 specific tasks → simple
   - 3-4 related areas → medium
   - 5+ areas or "comprehensive" → complex
3. **Specificity**: More specific requests are usually simpler than broad requests

EXAMPLES:
- "I need help with social media strategy only" → simple
- "I need social media and business strategy" → medium  
- "I need comprehensive analysis of everything" → complex

Return only: simple, medium, or complex
"""

            logger.info(f"🤖 LLM ORCHESTRATION: Sending simplified task complexity prompt to Ollama")
            logger.info(f"🤖 LLM ORCHESTRATION: Using model: {self.model}")

            # Remove all restrictions
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
                # No temperature, max_tokens, or stop tokens restrictions
            )

            # Log the raw Ollama response
            logger.info(f"🤖 LLM ORCHESTRATION: Raw Ollama complexity response: {json.dumps(response, default=str)}")

            complexity = response.get("message", {}).get("content", "medium").strip().lower()
            logger.info(f"🤖 LLM ORCHESTRATION: Ollama complexity response: '{complexity}'")

            # Validate complexity level
            if complexity not in ["simple", "medium", "complex"]:
                complexity = "medium"  # Default fallback
                logger.warning(f"🤖 LLM ORCHESTRATION: Invalid complexity level '{complexity}', using default 'medium'")

            logger.info(f"🤖 LLM ORCHESTRATION: Task complexity analyzed as '{complexity}'")
            return complexity

        except Exception as e:
            logger.error(f"🤖 LLM ORCHESTRATION: Error analyzing task complexity: {str(e)}")
            logger.error(f"🤖 LLM ORCHESTRATION: Exception type: {type(e).__name__}")
            return "medium"  # Default fallback

    async def select_agents_llm(self, task_description: str, user_context: Dict[str, Any],
                                available_agents: List[AIAgent]) -> List[Dict[str, Any]]:
        try:
            agent_profiles = self._format_agent_profiles(available_agents)

            # Intelligent prompt that lets LLM make decisions based on content
            prompt = f"""
You are an AI agent orchestrator. Your task is to select the most appropriate agents for this request.

TASK: "{task_description}"

AVAILABLE AGENTS:
{agent_profiles}

Analyze the task requirements and available agents. Based on the content and complexity of the task, select the agents that would provide the most effective and comprehensive solution.

Consider the scope, depth, and requirements of the task when making your selection.

Return a JSON array of selected agents:
[
    {{
        "agent_id": <agent_id>,
        "agent_type": "<agent_type>",
        "role": "primary",
        "reasoning": "<your reasoning for selecting this agent>",
        "priority": <1-2, where 1 is highest priority>
    }}
]
"""

            logger.info(f"🤖 LLM ORCHESTRATION: Sending enhanced task-specific prompt to Ollama for agent selection")
            logger.info(f"🤖 LLM ORCHESTRATION: Using model: {self.model}")

            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            # Log the raw Ollama response
            logger.info(f"🤖 LLM ORCHESTRATION: Raw Ollama response: {json.dumps(response, default=str)}")

            content = response.get("message", {}).get("content", "")
            logger.info(f"🤖 LLM ORCHESTRATION: Ollama content response: {content}")

            # Enhanced JSON parsing to handle markdown-wrapped responses
            try:
                # First, try to extract JSON from markdown code blocks
                if "```json" in content and "```" in content:
                    # Extract JSON from markdown code blocks
                    start_marker = "```json"
                    end_marker = "```"
                    start_idx = content.find(start_marker) + len(start_marker)
                    end_idx = content.rfind(end_marker)
                    json_str = content[start_idx:end_idx].strip()
                    selected_agents = json.loads(json_str)
                    logger.info(f"🤖 LLM ORCHESTRATION: Successfully parsed JSON from markdown blocks")
                elif "```" in content and "```" in content:
                    # Extract JSON from generic code blocks
                    start_marker = "```"
                    end_marker = "```"
                    start_idx = content.find(start_marker) + len(start_marker)
                    end_idx = content.rfind(end_marker)
                    json_str = content[start_idx:end_idx].strip()
                    # Remove language identifier if present
                    if json_str.startswith("json"):
                        json_str = json_str[4:].strip()
                    selected_agents = json.loads(json_str)
                    logger.info(f"🤖 LLM ORCHESTRATION: Successfully parsed JSON from generic code blocks")
                else:
                    # Try to parse the entire response as JSON
                    selected_agents = json.loads(content)
                    logger.info(f"🤖 LLM ORCHESTRATION: Successfully parsed direct JSON response")
            except json.JSONDecodeError as e:
                logger.error(f"🤖 LLM ORCHESTRATION: Failed to parse JSON response: {content}")
                logger.error(f"🤖 LLM ORCHESTRATION: JSON decode error: {str(e)}")
                # Fallback to database selection
                return self._fallback_agent_selection(available_agents, task_description)

            # Validate and enrich the selection
            validated_selection = self._validate_agent_selection(selected_agents, available_agents)

            # TEMPORARILY BYPASS ENFORCEMENT - RELY ON PURE LLM DECISION
            # validated_selection = self._enforce_selection_limits(validated_selection, task_description)

            # Log the selected agents for this task
            agent_ids = [agent['agent_id'] for agent in validated_selection]
            agent_names = [agent['name'] for agent in validated_selection]
            logger.info(f"🤖 LLM ORCHESTRATION: Selected agents for task '{task_description[:50]}...': IDs={agent_ids}, Names={agent_names}")

            logger.info(f"🤖 LLM ORCHESTRATION: Selected {len(validated_selection)} agents using LLM")
            return validated_selection

        except Exception as e:
            logger.error(f"🤖 LLM ORCHESTRATION: Error in LLM agent selection: {str(e)}")
            logger.error(f"🤖 LLM ORCHESTRATION: Exception type: {type(e).__name__}")
            return self._fallback_agent_selection(available_agents, task_description)

    async def plan_agent_orchestration(self, selected_agents: List[Dict[str, Any]],
                                      task_description: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to plan agent execution sequence and handoffs"""
        try:
            # Convert selected_agents to JSON-serializable format
            serializable_agents = []
            for agent in selected_agents:
                serializable_agent = {}
                for key, value in agent.items():
                    if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                        serializable_agent[key] = value
                    else:
                        serializable_agent[key] = str(value)
                serializable_agents.append(serializable_agent)

            # Enhanced prompt with scope-aware orchestration planning
            prompt = f"""
Create an orchestration plan for these agents working on this task.

SELECTED AGENTS: {json.dumps(serializable_agents, indent=2, default=str)}
TASK: {task_description}

ORCHESTRATION GUIDELINES:
1. **Scope Awareness**: If the task mentions "only", "just", "specifically", keep the plan focused and minimal
2. **Efficiency**: Minimize unnecessary handoffs and dependencies for simple tasks
3. **Parallel Execution**: For simple tasks, allow agents to work in parallel when possible
4. **Focused Output**: Ensure each agent's output directly addresses the user's stated needs

Return a JSON object with the orchestration plan:
{{
    "execution_sequence": [
        {{
            "agent_id": <agent_id>,
            "step": <step_number>,
            "dependencies": [<dependent_agent_ids>],
            "expected_output": "<what this agent should produce>",
            "handoff_conditions": ["<conditions for handoff>"]
        }}
    ],
    "data_flow": [
        {{
            "from_agent": <agent_id>,
            "to_agent": <agent_id>,
            "data_type": "<type of data to pass>",
            "format": "<data format>"
        }}
    ],
    "conflict_resolution": {{
        "strategy": "<resolution approach>",
        "fallback_agent": <agent_id>
    }},
    "success_metrics": ["<metric1>", "<metric2>"]
}}

IMPORTANT: Keep the plan simple and focused for specific requests. Avoid over-engineering.
"""

            logger.info(f"🤖 LLM ORCHESTRATION: Sending simplified orchestration planning prompt to Ollama")
            logger.info(f"🤖 LLM ORCHESTRATION: Using model: {self.model}")

            # Remove all restrictions
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
                # No temperature, max_tokens, or stop tokens restrictions
            )

            # Log the raw Ollama response
            logger.info(f"🤖 LLM ORCHESTRATION: Raw Ollama orchestration response: {json.dumps(response, default=str)}")

            content = response.get("message", {}).get("content", "")
            logger.info(f"🤖 LLM ORCHESTRATION: Ollama orchestration content response: {content}")

            # Enhanced JSON parsing to handle markdown-wrapped responses
            try:
                orchestration_plan = self._parse_json_from_markdown(content)

                logger.info(f"🤖 LLM ORCHESTRATION: Successfully parsed orchestration JSON response")

            except json.JSONDecodeError as e:
                logger.error(f"🤖 LLM ORCHESTRATION: Failed to parse orchestration plan JSON: {content}")
                logger.error(f"�� LLM ORCHESTRATION: JSON decode error: {str(e)}")
                return self._fallback_orchestration_plan(selected_agents)
            except Exception as e:
                logger.error(f"🤖 LLM ORCHESTRATION: Error extracting orchestration JSON: {str(e)}")
                logger.error(f"🤖 LLM ORCHESTRATION: Exception type: {type(e).__name__}")
                return self._fallback_orchestration_plan(selected_agents)

            logger.info(f"🤖 LLM ORCHESTRATION: Created orchestration plan with {len(orchestration_plan.get('execution_sequence', []))} steps")
            return orchestration_plan

        except Exception as e:
            logger.error(f"🤖 LLM ORCHESTRATION: Error in orchestration planning: {str(e)}")
            logger.error(f"🤖 LLM ORCHESTRATION: Exception type: {type(e).__name__}")
            return self._fallback_orchestration_plan(selected_agents)

    def _format_agent_profiles(self, agents: List[AIAgent]) -> str:
        """Format agent profiles for LLM consumption"""
        profiles = []
        for agent in agents:
            capabilities = agent.capabilities or {}
            capability_list = [cap for cap, enabled in capabilities.items() if enabled]

            profile = f"""
            Agent ID: {agent.id}
            Name: {agent.name}
            Type: {agent.agent_type}
            Status: {agent.status}
            Capabilities: {', '.join(capability_list)}
            """
            profiles.append(profile)

        return "\n".join(profiles)

    def _validate_agent_selection(self, selected_agents: List[Dict], available_agents: List[AIAgent]) -> List[Dict]:
        """Validate and enrich agent selection"""
        valid_agents = {agent.id: agent for agent in available_agents}
        validated_selection = []

        for selection in selected_agents:
            agent_id = selection.get("agent_id")
            if agent_id in valid_agents:
                agent = valid_agents[agent_id]
                validated_selection.append({
                    "agent_id": agent_id,
                    "agent_type": agent.agent_type,
                    "name": agent.name,
                    "role": selection.get("role", "supporting"),
                    "reasoning": selection.get("reasoning", "Selected by LLM"),
                    "priority": selection.get("priority", 3),
                    "capabilities": agent.capabilities
                })

        return validated_selection

    def _enforce_selection_limits(self, selected_agents: List[Dict[str, Any]], task_description: str) -> List[Dict[str, Any]]:
        """Enforce selection limits based on user request analysis"""
        try:
            task_lower = task_description.lower()
            
            # Count explicit tasks mentioned
            task_count = 0
            if "social media" in task_lower:
                task_count += 1
            if "business" in task_lower:
                task_count += 1
            if "content" in task_lower:
                task_count += 1
            if "analytics" in task_lower or "performance" in task_lower:
                task_count += 1
            if "growth" in task_lower:
                task_count += 1
            
            # Check for limiting words
            has_limiting_words = any(word in task_lower for word in ["only", "just", "specifically", "focused"])
            
            # Determine maximum allowed agents
            if has_limiting_words:
                max_agents = min(task_count, 2)  # Strict limit for "only" requests
            else:
                max_agents = min(task_count + 1, 7)  # Allow more agents for comprehensive requests
            
            # If no specific tasks detected, default to 2-3 agents
            if task_count == 0:
                max_agents = 3
            
            # Enforce the limit
            if len(selected_agents) > max_agents:
                logger.warning(f"🤖 LLM ORCHESTRATION: Enforcing selection limit. LLM selected {len(selected_agents)} agents, limiting to {max_agents}")
                # Keep only the highest priority agents
                selected_agents = sorted(selected_agents, key=lambda x: x.get('priority', 3))[:max_agents]
                
                # Update reasoning to reflect enforcement
                for agent in selected_agents:
                    agent['reasoning'] = f"Selected due to enforcement limit. Original: {agent.get('reasoning', '')}"
            
            logger.info(f"🤖 LLM ORCHESTRATION: Task count: {task_count}, Limiting words: {has_limiting_words}, Max agents: {max_agents}, Final selection: {len(selected_agents)}")
            
            return selected_agents
            
        except Exception as e:
            logger.error(f"🤖 LLM ORCHESTRATION: Error in selection enforcement: {str(e)}")
            return selected_agents

    def _fallback_agent_selection(self, available_agents: List[AIAgent], task_description: str) -> List[Dict[str, Any]]:
        """Fallback agent selection when LLM fails"""
        logger.warning("🤖 LLM ORCHESTRATION: Using fallback agent selection")

        # Simple keyword-based fallback
        task_lower = task_description.lower()

        if any(word in task_lower for word in ["growth", "audience", "followers"]):
            agent_type = "growth_advisor"
        elif any(word in task_lower for word in ["business", "monetization", "revenue"]):
            agent_type = "business_advisor"
        elif any(word in task_lower for word in ["content", "posting", "creative"]):
            agent_type = "content_advisor"
        elif any(word in task_lower for word in ["analytics", "performance", "metrics"]):
            agent_type = "analytics_advisor"
        else:
            agent_type = "growth_advisor"  # Default

        # Find matching agents
        matching_agents = [agent for agent in available_agents if agent.agent_type == agent_type]

        if not matching_agents:
            matching_agents = available_agents[:2]  # Take first 2 agents as fallback

        return [
            {
                "agent_id": agent.id,
                "agent_type": agent.agent_type,
                "name": agent.name,
                "role": "primary" if i == 0 else "supporting",
                "reasoning": "Fallback selection due to LLM failure",
                "priority": 1 if i == 0 else 2,
                "capabilities": agent.capabilities
            }
            for i, agent in enumerate(matching_agents)
        ]

    def _fallback_orchestration_plan(self, selected_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback orchestration plan when LLM fails"""
        logger.warning("🤖 LLM ORCHESTRATION: Using fallback orchestration plan")

        execution_sequence = []
        for i, agent in enumerate(selected_agents):
            execution_sequence.append({
                "agent_id": agent["agent_id"],
                "step": i + 1,
                "dependencies": [],
                "expected_output": f"Analysis and recommendations from {agent['agent_type']}",
                "handoff_conditions": ["task_completed"]
            })

        return {
            "execution_sequence": execution_sequence,
            "data_flow": [],
            "conflict_resolution": {
                "strategy": "sequential_execution",
                "fallback_agent": selected_agents[0]["agent_id"] if selected_agents else None
            },
            "success_metrics": ["task_completion", "response_quality"]
        }
