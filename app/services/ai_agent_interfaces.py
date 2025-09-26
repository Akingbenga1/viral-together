"""
AI Agent Interfaces following SOLID principles
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class IDataRetriever(ABC):
    """Interface for data retrieval operations"""
    
    @abstractmethod
    async def retrieve_data(self, query: str, agent_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant data based on query and agent type"""
        pass


class IContextManager(ABC):
    """Interface for context management operations"""
    
    @abstractmethod
    async def get_smart_context(self, user_query: str, agent_type: str, max_tokens: int = 1000) -> str:
        """Get smart context using vector search"""
        pass
    
    @abstractmethod
    async def store_context(self, data: List[Dict[str, Any]], agent_type: str) -> None:
        """Store data in vector database"""
        pass


class IToolCaller(ABC):
    """Interface for tool calling operations"""
    
    @abstractmethod
    async def get_available_tools(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get available tools for agent type"""
        pass
    
    @abstractmethod
    async def execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        pass


class IPromptBuilder(ABC):
    """Interface for prompt building operations"""
    
    @abstractmethod
    def build_prompt(self, user_query: str, context: str, agent_type: str) -> str:
        """Build optimized prompt with context"""
        pass


class IAIExecutor(ABC):
    """Interface for AI execution operations"""
    
    @abstractmethod
    async def execute_with_tools(self, prompt: str, tools: List[Dict[str, Any]], agent_type: str) -> str:
        """Execute AI with tool calling support"""
        pass


class IEnhancedAIAgent(ABC):
    """Interface for enhanced AI agent operations"""
    
    @abstractmethod
    async def process_request(self, user_id: int, agent_type: str, user_query: str) -> Dict[str, Any]:
        """Process user request with enhanced architecture"""
        pass
