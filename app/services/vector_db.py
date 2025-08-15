import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import numpy as np
import hashlib
import os
from typing import List, Dict, Any
import uuid
from datetime import datetime

class VectorDatabaseService:
    def __init__(self):
        # Initialize Qdrant client
        self.client = QdrantClient(":memory:")  # In-memory for development, can be changed to URL for production
        
        # Vector dimension for simple hash-based embeddings
        self.vector_dim = 128
        
        # Collection names
        self.user_conversations_collection = "user_conversations"
        self.agent_contexts_collection = "agent_contexts"
        
        # Initialize collections
        self._init_collections()
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Generate a simple hash-based embedding for text"""
        # Create a hash of the text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to a fixed-size vector
        vector = []
        for i in range(0, len(text_hash), 2):
            if len(vector) >= self.vector_dim:
                break
            # Convert hex pair to float between -1 and 1
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0 * 2 - 1
            vector.append(value)
        
        # Pad or truncate to exact dimension
        while len(vector) < self.vector_dim:
            vector.append(0.0)
        
        return vector[:self.vector_dim]
    
    def _init_collections(self):
        """Initialize Qdrant collections"""
        # Create user conversations collection
        try:
            self.client.get_collection(self.user_conversations_collection)
        except:
            self.client.create_collection(
                collection_name=self.user_conversations_collection,
                vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
            )
        
        # Create agent contexts collection
        try:
            self.client.get_collection(self.agent_contexts_collection)
        except:
            self.client.create_collection(
                collection_name=self.agent_contexts_collection,
                vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
            )

    def store_user_conversation(self, user_id: int, conversation_text: str, 
                                conversation_type: str = "general", metadata: Dict = None) -> str:
        """Store user conversation in vector database"""
        conversation_uuid = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self._generate_simple_embedding(conversation_text)
        
        # Prepare payload
        payload = {
            "user_id": user_id,
            "conversation_type": conversation_type,
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_uuid": conversation_uuid,
            "conversation_text": conversation_text
        }
        if metadata:
            payload.update(metadata)
        
        # Add to collection
        self.client.upsert(
            collection_name=self.user_conversations_collection,
            points=[
                PointStruct(
                    id=conversation_uuid,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return conversation_uuid

    def retrieve_user_conversations(self, user_id: int, query: str = None, 
                                    limit: int = 10, conversation_type: str = None) -> List[Dict]:
        """Retrieve user conversations with optional similarity search"""
        # Build filter
        filter_conditions = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        if conversation_type:
            filter_conditions.append(FieldCondition(key="conversation_type", match=MatchValue(value=conversation_type)))
        
        filter_query = Filter(must=filter_conditions) if filter_conditions else None
        
        if query:
            # Similarity search
            query_embedding = self._generate_simple_embedding(query)
            results = self.client.search(
                collection_name=self.user_conversations_collection,
                query_vector=query_embedding,
                query_filter=filter_query,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            conversations = []
            for result in results:
                conversation = {
                    "conversation_uuid": result.id,
                    "conversation_text": result.payload.get("conversation_text", ""),
                    "metadata": result.payload,
                    "similarity_score": result.score
                }
                conversations.append(conversation)
        else:
            # Get recent conversations
            results = self.client.scroll(
                collection_name=self.user_conversations_collection,
                scroll_filter=filter_query,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            conversations = []
            for result in results[0]:  # scroll returns (points, next_page_offset)
                conversation = {
                    "conversation_uuid": result.id,
                    "conversation_text": result.payload.get("conversation_text", ""),
                    "metadata": result.payload,
                    "similarity_score": None
                }
                conversations.append(conversation)
        
        return conversations

    def store_agent_context(self, agent_uuid: str, context_text: str, 
                            context_type: str = "memory", metadata: Dict = None) -> str:
        """Store AI agent context in vector database"""
        context_uuid = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self._generate_simple_embedding(context_text)
        
        # Prepare payload
        payload = {
            "agent_uuid": agent_uuid,
            "context_type": context_type,
            "timestamp": datetime.utcnow().isoformat(),
            "context_uuid": context_uuid,
            "context_text": context_text
        }
        if metadata:
            payload.update(metadata)
        
        # Add to collection
        self.client.upsert(
            collection_name=self.agent_contexts_collection,
            points=[
                PointStruct(
                    id=context_uuid,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return context_uuid

    def retrieve_agent_context(self, agent_uuid: str, query: str = None, 
                               limit: int = 10, context_type: str = None) -> List[Dict]:
        """Retrieve AI agent context with optional similarity search"""
        # Build filter
        filter_conditions = [FieldCondition(key="agent_uuid", match=MatchValue(value=agent_uuid))]
        if context_type:
            filter_conditions.append(FieldCondition(key="context_type", match=MatchValue(value=context_type)))
        
        filter_query = Filter(must=filter_conditions) if filter_conditions else None
        
        if query:
            # Similarity search
            query_embedding = self._generate_simple_embedding(query)
            results = self.client.search(
                collection_name=self.agent_contexts_collection,
                query_vector=query_embedding,
                query_filter=filter_query,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            contexts = []
            for result in results:
                context = {
                    "context_uuid": result.id,
                    "context_text": result.payload.get("context_text", ""),
                    "metadata": result.payload,
                    "similarity_score": result.score
                }
                contexts.append(context)
        else:
            # Get recent contexts
            results = self.client.scroll(
                collection_name=self.agent_contexts_collection,
                scroll_filter=filter_query,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            contexts = []
            for result in results[0]:  # scroll returns (points, next_page_offset)
                context = {
                    "context_uuid": result.id,
                    "context_text": result.payload.get("context_text", ""),
                    "metadata": result.payload,
                    "similarity_score": None
                }
                contexts.append(context)
        
        return contexts
