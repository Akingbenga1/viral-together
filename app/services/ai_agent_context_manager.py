"""
AI Agent Context Manager following SOLID principles
"""

import logging
from typing import Dict, Any, List
from app.services.ai_agent_interfaces import IContextManager
from app.services.vector_db import VectorDatabaseService

logger = logging.getLogger(__name__)


class AIAgentContextManager(IContextManager):
    """AI Agent context manager implementation"""
    
    def __init__(self, vector_db: VectorDatabaseService):
        self.vector_db = vector_db
    
    async def get_smart_context(self, user_query: str, agent_type: str, max_tokens: int = 1000) -> str:
        """Get smart context using vector search"""
        try:
            logger.info(f"AIAgentContextManager: Getting smart context for query '{user_query}' with agent type '{agent_type}' (max_tokens: {max_tokens})")
            
            # Search vector database for relevant data
            relevant_data = self.vector_db.retrieve_agent_context(
                agent_uuid=f"agent_{agent_type}",
                query=user_query,
                limit=3  # Get top 3 most relevant results
            )
            
            # Format context for AI consumption
            context = self._format_context_for_ai(relevant_data)
            
            # Trim to fit token limit
            if len(context) > max_tokens:
                context = context[:max_tokens]
                logger.info(f"AIAgentContextManager: Trimmed context to {max_tokens} tokens")
            
            logger.info(f"AIAgentContextManager: Generated smart context with {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"AIAgentContextManager: Failed to get smart context: {e}")
            return ""
    
    async def store_context(self, data: List[Dict[str, Any]], agent_type: str) -> None:
        """Store data in vector database"""
        try:
            logger.info(f"AIAgentContextManager: Storing {len(data)} items for agent type '{agent_type}'")
            
            for item in data:
                # Store each item in vector database
                self.vector_db.store_agent_context(
                    agent_uuid=f"agent_{agent_type}",
                    context_text=f"{item.get('title', '')} {item.get('content', '')}",
                    context_type="search_result",
                    metadata=item
                )
            
            logger.info(f"AIAgentContextManager: Successfully stored {len(data)} items")
            
        except Exception as e:
            logger.error(f"AIAgentContextManager: Failed to store context: {e}")
    
    def _format_context_for_ai(self, relevant_data: List[Dict[str, Any]]) -> str:
        """Format relevant data for AI consumption"""
        if not relevant_data:
            return "No relevant context available"
        
        formatted_context = []
        for item in relevant_data:
            context_text = item.get('context_text', '')
            similarity_score = item.get('similarity_score', 0.0)
            
            formatted_context.append(f"Relevance: {similarity_score:.2f} - {context_text}")
        
        return "\n".join(formatted_context)
