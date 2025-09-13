from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
from app.db.models.user_agent_association import UserAgentAssociation
from app.db.models.ai_agent import AIAgent
from app.db.models.user import User
from app.schemas.user_agent_association import UserAgentAssociationCreate
from app.core.query_helpers import safe_scalar_one_or_none

class UserAgentAssociationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user_agent_association(self, user_id: int, agent_id: int, association_type: str = None, 
                                          is_primary: bool = False, priority: int = None, assigned_by: int = None) -> bool:
        """Create user agent association"""
        import uuid
        
        db_association = UserAgentAssociation(
            uuid=uuid.uuid4(),  # Generate UUID explicitly
            user_id=user_id,
            agent_id=agent_id,
            association_type=association_type,
            is_primary=is_primary,
            priority=priority,
            status="active",
            assigned_by=assigned_by
        )
        self.db.add(db_association)
        await self.db.commit()
        await self.db.refresh(db_association)
        return True

    async def remove_user_agent_association(self, user_id: int, agent_id: int) -> bool:
        """Remove user agent association"""
        query = select(UserAgentAssociation).where(
            UserAgentAssociation.user_id == user_id,
            UserAgentAssociation.agent_id == agent_id,
            UserAgentAssociation.status == "active"
        )
        result = await self.db.execute(query)
        association = await safe_scalar_one_or_none(result)
        
        if association:
            association.status = "inactive"
            await self.db.commit()
            return True
        return False

    async def get_user_agents(self, user_id: int) -> List[Dict]:
        """Get user's agents"""
        try:
            # First get the associations
            query = select(UserAgentAssociation).where(
                UserAgentAssociation.user_id == user_id,
                UserAgentAssociation.status == "active"
            )
            
            result = await self.db.execute(query)
            associations = result.scalars().all()
            
            # Then get the agents separately to avoid relationship issues
            agent_ids = [assoc.agent_id for assoc in associations]
            if not agent_ids:
                return []
                
            agent_query = select(AIAgent).where(AIAgent.id.in_(agent_ids))
            agent_result = await self.db.execute(agent_query)
            agents = {agent.id: agent for agent in agent_result.scalars().all()}
            
            return [
                {
                    "association_id": association.id,
                    "association_uuid": str(association.uuid),
                    "association_type": association.association_type,
                    "is_primary": association.is_primary,
                    "priority": association.priority,
                    "agent_id": association.agent_id,
                    "agent_uuid": str(agents[association.agent_id].uuid) if association.agent_id in agents else None,
                    "agent_name": agents[association.agent_id].name if association.agent_id in agents else None,
                    "agent_type": agents[association.agent_id].agent_type if association.agent_id in agents else None,
                    "agent_capabilities": agents[association.agent_id].capabilities if association.agent_id in agents else None,
                    "agent_status": agents[association.agent_id].status if association.agent_id in agents else None,
                    "assigned_at": association.assigned_at.isoformat() if association.assigned_at else None,
                    "assigned_by": association.assigned_by,
                    "created_at": association.created_at.isoformat() if association.created_at else None
                }
                for association in associations
                if association.agent_id in agents
            ]
        except Exception as e:
            print(f"Error in get_user_agents: {e}")
            return []

    async def get_agent_users(self, agent_id: int) -> List[Dict]:
        """Get agent's users"""
        query = select(UserAgentAssociation, User).join(
            User, UserAgentAssociation.user_id == User.id
        ).where(
            UserAgentAssociation.agent_id == agent_id,
            UserAgentAssociation.status == "active"
        )
        
        result = await self.db.execute(query)
        associations = result.all()
        
        return [
            {
                "association_id": association.id,
                "association_uuid": str(association.uuid),
                "association_type": association.association_type,
                "is_primary": association.is_primary,
                "priority": association.priority,
                "user_id": user.id,
                "user_uuid": str(user.uuid),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "assigned_at": association.assigned_at.isoformat(),
                "assigned_by": association.assigned_by,
                "created_at": association.created_at.isoformat()
            }
            for association, user in associations
        ]

    async def get_user_primary_agent(self, user_id: int) -> Optional[Dict]:
        """Get user's primary agent"""
        query = select(UserAgentAssociation, AIAgent).join(
            AIAgent, UserAgentAssociation.agent_id == AIAgent.id
        ).where(
            UserAgentAssociation.user_id == user_id,
            UserAgentAssociation.is_primary == True,
            UserAgentAssociation.status == "active"
        )
        
        result = await self.db.execute(query)
        associations = result.all()
        
        if associations:
            association, agent = associations[0]  # Get the first (and should be only) result
            return {
                "association_id": association.id,
                "association_uuid": str(association.uuid),
                "association_type": association.association_type,
                "is_primary": association.is_primary,
                "priority": association.priority,
                "agent_id": agent.id,
                "agent_uuid": str(agent.uuid),
                "agent_name": agent.name,
                "agent_type": agent.agent_type,
                "agent_capabilities": agent.capabilities,
                "agent_status": agent.status,
                "assigned_at": association.assigned_at.isoformat(),
                "assigned_by": association.assigned_by,
                "created_at": association.created_at.isoformat()
            }
        return None
