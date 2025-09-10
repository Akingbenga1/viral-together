from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
import json
import ollama
from app.db.models.ai_agent import AIAgent
from app.db.models.ai_agent_response import AIAgentResponse
from app.services.vector_db import VectorDatabaseService
from app.services.llm_orchestration_service import LLMOrchestrationService
from app.schemas.coordination import CoordinationSessionCreate, TaskAssignment, AgentContextRequest, AgentContextResponse
from app.core.config import settings

class AgentCoordinatorService:
    def __init__(self, db: AsyncSession, vector_db: VectorDatabaseService):
        self.db = db
        self.vector_db = vector_db
        self.coordination_sessions = {}  # Simple in-memory storage
        self.llm_orchestrator = LLMOrchestrationService() if settings.AI_AGENT_LLM_ORCHESTRATION_ENABLED else None

    async def create_coordination_session(self, user_id: int, task_type: str, initial_context: Dict) -> str:
        """Create coordination session"""
        coordination_uuid = str(uuid.uuid4())
        self.coordination_sessions[coordination_uuid] = {
            "user_id": user_id,
            "task_type": task_type,
            "initial_context": initial_context,
            "status": "active"
        }
        return coordination_uuid

    async def assign_task_to_agent(self, coordination_uuid: str, agent_id: int, task_details: Dict) -> bool:
        """Assign task to agent"""
        if coordination_uuid not in self.coordination_sessions:
            return False
        
        self.coordination_sessions[coordination_uuid]["current_agent_id"] = agent_id
        self.coordination_sessions[coordination_uuid]["task_details"] = task_details
        return True

    async def handoff_task(self, coordination_uuid: str, from_agent_id: int, to_agent_id: int, handoff_data: Dict) -> bool:
        """Handoff task between agents"""
        if coordination_uuid not in self.coordination_sessions:
            return False
        
        self.coordination_sessions[coordination_uuid]["current_agent_id"] = to_agent_id
        self.coordination_sessions[coordination_uuid]["handoff_data"] = handoff_data
        return True

    async def get_available_agents(self, user_id: int, task_requirements: Dict) -> List[AIAgent]:
        """Get available agents using hybrid approach based on configuration"""
        
        # Get all active agents from database
        query = select(AIAgent).where(
            AIAgent.status == "active",
            AIAgent.is_active == True
        )
        result = await self.db.execute(query)
        all_agents = result.scalars().all()
        
        print(f"🔍 DEBUG: Found {len(all_agents)} total active agents")
        for agent in all_agents:
            print(f"🔍 DEBUG: Agent {agent.id} - {agent.name} - {agent.agent_type} - Capabilities: {agent.capabilities}")
        
        # Determine orchestration mode
        orchestration_mode = settings.AI_AGENT_ORCHESTRATION_MODE.lower()
        
        if orchestration_mode == "database":
            return await self._database_agent_selection(all_agents, task_requirements)
        elif orchestration_mode == "llm":
            return await self._llm_agent_selection(all_agents, task_requirements, user_id)
        elif orchestration_mode == "hybrid":
            return await self._hybrid_agent_selection(all_agents, task_requirements, user_id)
        else:
            # Default to database selection
            return await self._database_agent_selection(all_agents, task_requirements)

    async def _database_agent_selection(self, all_agents: List[AIAgent], task_requirements: Dict) -> List[AIAgent]:
        """Database-driven agent selection (original method)"""
        print(f"🔍 DEBUG: Using database-driven agent selection")
        
        # Filter by capabilities if specified
        if "capability" in task_requirements:
            required_capability = task_requirements["capability"]
            print(f"🔍 DEBUG: Looking for capability: {required_capability}")
            filtered_agents = []
            for agent in all_agents:
                # Check if the agent has the required capability
                if (agent.capabilities and 
                    isinstance(agent.capabilities, dict) and 
                    required_capability in agent.capabilities and 
                    agent.capabilities[required_capability]):
                    filtered_agents.append(agent)
                    print(f"🔍 DEBUG: Agent {agent.id} matches capability {required_capability}")
            return filtered_agents
        
        return all_agents

    async def _llm_agent_selection(self, all_agents: List[AIAgent], task_requirements: Dict, user_id: int) -> List[AIAgent]:
        """LLM-driven agent selection"""
        print(f"🔍 DEBUG: Using LLM-driven agent selection")
        
        if not self.llm_orchestrator:
            print(f"🔍 DEBUG: LLM orchestrator not available, falling back to database selection")
            return await self._database_agent_selection(all_agents, task_requirements)
        
        try:
            # Extract task description from requirements
            task_description = task_requirements.get("task_description", "influencer analysis")
            user_context = task_requirements.get("user_context", {})
            
            # Use LLM to select agents
            selected_agents_data = await self.llm_orchestrator.select_agents_llm(
                task_description=task_description,
                user_context=user_context,
                available_agents=all_agents
            )
            
            # Convert back to AIAgent objects
            selected_agents = []
            for agent_data in selected_agents_data:
                agent_id = agent_data.get("agent_id")
                agent = next((a for a in all_agents if a.id == agent_id), None)
                if agent:
                    selected_agents.append(agent)
                    print(f"🔍 DEBUG: LLM selected agent {agent.id} - {agent.name} - {agent.agent_type}")
            
            return selected_agents if selected_agents else all_agents[:2]  # Fallback to first 2 agents
            
        except Exception as e:
            print(f"🔍 DEBUG: LLM agent selection failed: {str(e)}, falling back to database selection")
            return await self._database_agent_selection(all_agents, task_requirements)

    async def _hybrid_agent_selection(self, all_agents: List[AIAgent], task_requirements: Dict, user_id: int) -> List[AIAgent]:
        """Hybrid agent selection based on task complexity"""
        print(f"🔍 DEBUG: Using hybrid agent selection")
        
        if not self.llm_orchestrator:
            print(f"🔍 DEBUG: LLM orchestrator not available, using database selection")
            return await self._database_agent_selection(all_agents, task_requirements)
        
        try:
            # Analyze task complexity
            task_description = task_requirements.get("task_description", "influencer analysis")
            user_context = task_requirements.get("user_context", {})
            
            complexity = await self.llm_orchestrator.analyze_task_complexity(task_description, user_context)
            threshold = settings.AI_AGENT_TASK_COMPLEXITY_THRESHOLD.lower()
            
            print(f"🔍 DEBUG: Task complexity: {complexity}, threshold: {threshold}")
            
            # Determine selection method based on complexity
            if complexity == "simple" or (complexity == "medium" and threshold == "simple"):
                print(f"🔍 DEBUG: Using database selection for {complexity} task")
                return await self._database_agent_selection(all_agents, task_requirements)
            else:
                print(f"🔍 DEBUG: Using LLM selection for {complexity} task")
                return await self._llm_agent_selection(all_agents, task_requirements, user_id)
                
        except Exception as e:
            print(f"🔍 DEBUG: Hybrid agent selection failed: {str(e)}, using database selection")
            return await self._database_agent_selection(all_agents, task_requirements)

    async def coordinate_agents(self, coordination_uuid: str, task: Dict) -> Dict:
        """Coordinate multiple agents with enhanced orchestration"""
        if coordination_uuid not in self.coordination_sessions:
            return {"error": "Coordination session not found"}
        
        session = self.coordination_sessions[coordination_uuid]
        
        # Enhanced coordination with LLM orchestration if available
        if self.llm_orchestrator and settings.AI_AGENT_ORCHESTRATION_MODE.lower() in ["llm", "hybrid"]:
            try:
                # Get task details
                task_description = task.get("type", "influencer_analysis")
                user_context = session.get("initial_context", {})
                agent_responses = task.get("agent_responses", [])
                
                # Create orchestration plan
                orchestration_plan = await self.llm_orchestrator.plan_agent_orchestration(
                    selected_agents=agent_responses,
                    task_description=task_description,
                    user_context=user_context
                )
                
                return {
                    "coordination_uuid": coordination_uuid,
                    "status": "completed",
                    "result": "Task coordinated successfully with LLM orchestration",
                    "orchestration_plan": orchestration_plan,
                    "mode": settings.AI_AGENT_ORCHESTRATION_MODE
                }
            except Exception as e:
                print(f"🔍 DEBUG: LLM orchestration failed: {str(e)}, using simple coordination")
        
        # Simple coordination logic (original fallback)
        return {
            "coordination_uuid": coordination_uuid,
            "status": "completed",
            "result": "Task coordinated successfully",
            "mode": "database"
        }

    async def resolve_agent_conflicts(self, coordination_uuid: str, conflict_data: Dict) -> Dict:
        """Resolve agent conflicts with enhanced logic"""
        if coordination_uuid not in self.coordination_sessions:
            return {"error": "Coordination session not found"}
        
        # Enhanced conflict resolution with LLM if available
        if self.llm_orchestrator and settings.AI_AGENT_ORCHESTRATION_MODE.lower() in ["llm", "hybrid"]:
            try:
                # Use LLM to analyze conflicts and suggest resolution
                conflict_description = json.dumps(conflict_data, indent=2)
                prompt = f"""
                AGENT CONFLICT RESOLUTION
                
                Conflict Data: {conflict_description}
                
                Analyze the conflict and provide resolution strategy:
                1. Identify the root cause of the conflict
                2. Suggest the best resolution approach
                3. Recommend which agent should take precedence
                4. Provide steps to prevent similar conflicts
                
                Return a structured resolution plan.
                """
                
                # Assuming ollama is available and can be used for LLM calls
                # This part would require an actual LLM client implementation
                # For now, we'll simulate a response or raise an error if ollama is not defined
                # In a real scenario, you'd integrate with an LLM client (e.g., OpenAI, Ollama, etc.)
                # For this example, we'll just print the prompt and raise an error
                print(f"🔍 DEBUG: LLM conflict resolution prompt:\n{prompt}")
                # Example of how you might integrate with an LLM client (replace with actual call)
                client = ollama.Client(host=self.llm_orchestrator.base_url)
                response = client.chat(
                    model=self.llm_orchestrator.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.3, "max_tokens": 500}
                )
                
                resolution_plan = response.get("message", {}).get("content", "Proceed with primary agent")
                
                return {
                    "coordination_uuid": coordination_uuid,
                    "resolution": "Conflict resolved with LLM analysis",
                    "action": resolution_plan,
                    "mode": "llm"
                }
            except Exception as e:
                print(f"🔍 DEBUG: LLM conflict resolution failed: {str(e)}")
        
        # Simple conflict resolution (original fallback)
        return {
            "coordination_uuid": coordination_uuid,
            "resolution": "Conflict resolved",
            "action": "Proceed with primary agent",
            "mode": "database"
        }

    async def get_context_for_agent_task(self, user_id: int, current_prompt: str, agent_id: int, context_window: int = 10) -> Dict:
        """Get context for agent task"""
        # Get conversation history from vector DB
        conversation_history = self.vector_db.retrieve_user_conversations(
            user_id=user_id,
            query=current_prompt,
            limit=context_window
        )
        
        # Get agent's recent responses from relational DB
        query = select(AIAgentResponse).where(
            AIAgentResponse.agent_id == agent_id
        ).order_by(AIAgentResponse.created_at.desc()).limit(5)
        
        result = await self.db.execute(query)
        agent_responses = result.scalars().all()
        
        # Format agent responses
        formatted_responses = []
        for response in agent_responses:
            formatted_responses.append({
                "task_id": response.task_id,
                "response": response.response,
                "response_type": response.response_type,
                "created_at": response.created_at.isoformat()
            })
        
        return {
            "current_prompt": current_prompt,
            "conversation_history": conversation_history,
            "agent_responses": formatted_responses,
            "context_metadata": {
                "user_id": user_id,
                "agent_id": agent_id,
                "context_window": context_window
            }
        }
