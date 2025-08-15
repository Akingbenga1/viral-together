from typing import List, Dict, Optional
from app.services.vector_db import VectorDatabaseService

class UserConversationService:
    def __init__(self, vector_db: VectorDatabaseService):
        self.vector_db = vector_db

    async def store_user_conversation(self, user_id: int, conversation_text: str, 
                                     conversation_type: str = "general", metadata: Dict = None) -> str:
        """Store user conversation"""
        return self.vector_db.store_user_conversation(
            user_id=user_id,
            conversation_text=conversation_text,
            conversation_type=conversation_type,
            metadata=metadata
        )

    async def retrieve_user_conversations(self, user_id: int, query: str = None, 
                                         limit: int = 10, conversation_type: str = None) -> List[Dict]:
        """Retrieve user conversations"""
        return self.vector_db.retrieve_user_conversations(
            user_id=user_id,
            query=query,
            limit=limit,
            conversation_type=conversation_type
        )

    async def get_conversation_history(self, user_id: int, time_range: Dict = None) -> List[Dict]:
        """Get conversation history"""
        return self.vector_db.retrieve_user_conversations(
            user_id=user_id,
            limit=50  # Get more for history
        )

    async def store_agent_context(self, agent_uuid: str, context_text: str, 
                                 context_type: str = "memory", metadata: Dict = None) -> str:
        """Store agent context"""
        return self.vector_db.store_agent_context(
            agent_uuid=agent_uuid,
            context_text=context_text,
            context_type=context_type,
            metadata=metadata
        )

    async def retrieve_agent_context(self, agent_uuid: str, query: str = None, 
                                    limit: int = 10, context_type: str = None) -> List[Dict]:
        """Retrieve agent context"""
        return self.vector_db.retrieve_agent_context(
            agent_uuid=agent_uuid,
            query=query,
            limit=limit,
            context_type=context_type
        )
