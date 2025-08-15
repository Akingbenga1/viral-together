from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
from app.db.models.ai_agent import AIAgent
from app.db.models.ai_agent_response import AIAgentResponse
from app.services.vector_db import VectorDatabaseService
from app.schemas.coordination import CoordinationSessionCreate, TaskAssignment, AgentContextRequest, AgentContextResponse

class AgentCoordinatorService:
    def __init__(self, db: AsyncSession, vector_db: VectorDatabaseService):
        self.db = db
        self.vector_db = vector_db
        self.coordination_sessions = {}  # Simple in-memory storage

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
        """Get available agents for user"""
        query = select(AIAgent).where(
            AIAgent.user_id == user_id,
            AIAgent.status == "active",
            AIAgent.is_active == True
        )
        result = await self.db.execute(query)
        agents = result.scalars().all()
        
        # Filter by capabilities if specified
        if "capability" in task_requirements:
            filtered_agents = []
            for agent in agents:
                if "capabilities" in agent.capabilities and task_requirements["capability"] in agent.capabilities["capabilities"]:
                    filtered_agents.append(agent)
            return filtered_agents
        
        return agents

    async def coordinate_agents(self, coordination_uuid: str, task: Dict) -> Dict:
        """Coordinate multiple agents"""
        if coordination_uuid not in self.coordination_sessions:
            return {"error": "Coordination session not found"}
        
        session = self.coordination_sessions[coordination_uuid]
        # Simple coordination logic - can be expanded
        return {
            "coordination_uuid": coordination_uuid,
            "status": "completed",
            "result": "Task coordinated successfully"
        }

    async def resolve_agent_conflicts(self, coordination_uuid: str, conflict_data: Dict) -> Dict:
        """Resolve agent conflicts"""
        if coordination_uuid not in self.coordination_sessions:
            return {"error": "Coordination session not found"}
        
        # Simple conflict resolution - can be expanded
        return {
            "coordination_uuid": coordination_uuid,
            "resolution": "Conflict resolved",
            "action": "Proceed with primary agent"
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
