"""
Vector Database Data Retriever following SOLID principles
"""

import logging
from typing import Dict, Any, List
from app.services.ai_agent_interfaces import IDataRetriever
from app.services.vector_db import VectorDatabaseService

logger = logging.getLogger(__name__)


class VectorDataRetriever(IDataRetriever):
    """Vector database data retriever implementation"""
    
    def __init__(self, vector_db: VectorDatabaseService):
        self.vector_db = vector_db
    
    async def retrieve_data(self, query: str, agent_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant data using vector search"""
        try:
            logger.info(f"VectorDataRetriever: Searching for query '{query}' with agent type '{agent_type}' (limit: {limit})")
            
            # Search vector database for relevant data
            relevant_data = self.vector_db.retrieve_agent_context(
                agent_uuid=f"agent_{agent_type}",
                query=query,
                limit=limit
            )
            
            logger.info(f"VectorDataRetriever: Found {len(relevant_data)} relevant results")
            return relevant_data
            
        except Exception as e:
            logger.error(f"VectorDataRetriever: Failed to retrieve data: {e}")
            return []
