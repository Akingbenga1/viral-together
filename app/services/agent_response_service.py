from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
from app.db.models.ai_agent_response import AIAgentResponse
from app.schemas.ai_agent_response import AIAgentResponseCreate

class AgentResponseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_agent_response(self, agent_id: int, task_id: str, response: str, response_type: str = "task_response") -> bool:
        """Record agent response"""
        db_response = AIAgentResponse(
            agent_id=agent_id,
            task_id=task_id,
            response=response,
            response_type=response_type
        )
        self.db.add(db_response)
        await self.db.commit()
        await self.db.refresh(db_response)
        return True

    async def get_agent_responses(self, agent_id: int, limit: int = 50) -> List[Dict]:
        """Get agent responses"""
        query = select(AIAgentResponse).where(
            AIAgentResponse.agent_id == agent_id
        ).order_by(AIAgentResponse.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        responses = result.scalars().all()
        
        return [
            {
                "id": response.id,
                "uuid": str(response.uuid),
                "agent_id": response.agent_id,
                "task_id": response.task_id,
                "response": response.response,
                "response_type": response.response_type,
                "created_at": response.created_at.isoformat()
            }
            for response in responses
        ]

    async def get_task_responses(self, task_id: str) -> List[Dict]:
        """Get task responses"""
        query = select(AIAgentResponse).where(
            AIAgentResponse.task_id == task_id
        ).order_by(AIAgentResponse.created_at.asc())
        
        result = await self.db.execute(query)
        responses = result.scalars().all()
        
        return [
            {
                "id": response.id,
                "uuid": str(response.uuid),
                "agent_id": response.agent_id,
                "task_id": response.task_id,
                "response": response.response,
                "response_type": response.response_type,
                "created_at": response.created_at.isoformat()
            }
            for response in responses
        ]
