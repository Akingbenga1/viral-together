from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.dependencies import get_db, get_vector_db
from app.services.agent_coordinator_service import AgentCoordinatorService
from app.services.agent_response_service import AgentResponseService
from app.services.user_agent_association_service import UserAgentAssociationService
from app.services.user_conversation_service import UserConversationService
from app.schemas.ai_agent import AIAgent, AIAgentCreate, AIAgentUpdate
from app.schemas.ai_agent_response import AIAgentResponse, AIAgentResponseCreate
from app.schemas.user_agent_association import UserAgentAssociation, UserAgentAssociationCreate
from app.schemas.coordination import CoordinationSessionCreate, TaskAssignment, AgentContextRequest, AgentContextResponse

router = APIRouter(prefix="/ai-agents", tags=["AI Agents"])

# AI Agent endpoints
@router.post("/", response_model=AIAgent)
async def create_ai_agent(
    agent: AIAgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new AI agent"""
    # This would typically be implemented in a service
    # For now, return a mock response
    return {
        "id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "name": agent.name,
        "agent_type": agent.agent_type,
        "capabilities": agent.capabilities,
        "status": "active",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": None
    }

@router.get("/", response_model=List[AIAgent])
async def get_ai_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all AI agents"""
    from app.db.models.ai_agent import AIAgent as AIAgentModel
    
    result = await db.execute(
        select(AIAgentModel)
        .offset(skip)
        .limit(limit)
        .order_by(AIAgentModel.created_at.desc())
    )
    agents = result.scalars().all()
    return agents

@router.get("/{agent_id}", response_model=AIAgent)
async def get_ai_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific AI agent"""
    from app.db.models.ai_agent import AIAgent as AIAgentModel
    
    result = await db.execute(
        select(AIAgentModel).where(AIAgentModel.id == agent_id)
    )
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="AI agent not found")
    
    return agent

# Agent Response endpoints
@router.post("/responses", response_model=dict)
async def record_agent_response(
    response: AIAgentResponseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record an agent response"""
    response_service = AgentResponseService(db)
    success = await response_service.record_agent_response(
        agent_id=response.agent_id,
        task_id=response.task_id,
        response=response.response,
        response_type=response.response_type
    )
    return {"success": success}

@router.get("/responses/agent/{agent_id}", response_model=List[dict])
async def get_agent_responses(
    agent_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get agent responses"""
    response_service = AgentResponseService(db)
    return await response_service.get_agent_responses(agent_id, limit)

@router.get("/responses/task/{task_id}", response_model=List[dict])
async def get_task_responses(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get task responses"""
    response_service = AgentResponseService(db)
    return await response_service.get_task_responses(task_id)

# User-Agent Association endpoints
@router.post("/associations", response_model=dict)
async def create_user_agent_association(
    association: UserAgentAssociationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create user-agent association"""
    association_service = UserAgentAssociationService(db)
    success = await association_service.create_user_agent_association(
        user_id=association.user_id,
        agent_id=association.agent_id,
        association_type=association.association_type,
        is_primary=association.is_primary,
        priority=association.priority,
        assigned_by=association.assigned_by
    )
    return {"success": success}

@router.delete("/associations/{user_id}/{agent_id}", response_model=dict)
async def remove_user_agent_association(
    user_id: int,
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove user-agent association"""
    association_service = UserAgentAssociationService(db)
    success = await association_service.remove_user_agent_association(user_id, agent_id)
    return {"success": success}

@router.get("/associations/user/{user_id}", response_model=List[dict])
async def get_user_agents(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's agents"""
    association_service = UserAgentAssociationService(db)
    return await association_service.get_user_agents(user_id)

@router.get("/associations/agent/{agent_id}", response_model=List[dict])
async def get_agent_users(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get agent's users"""
    association_service = UserAgentAssociationService(db)
    return await association_service.get_agent_users(agent_id)

@router.get("/associations/user/{user_id}/primary", response_model=dict)
async def get_user_primary_agent(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's primary agent"""
    association_service = UserAgentAssociationService(db)
    primary_agent = await association_service.get_user_primary_agent(user_id)
    if not primary_agent:
        raise HTTPException(status_code=404, detail="No primary agent found for user")
    return primary_agent

# Coordination endpoints
@router.post("/coordination/sessions", response_model=dict)
async def create_coordination_session(
    session: CoordinationSessionCreate,
    db: AsyncSession = Depends(get_db),
    vector_db = Depends(get_vector_db)
):
    """Create coordination session"""
    coordinator = AgentCoordinatorService(db, vector_db)
    coordination_uuid = await coordinator.create_coordination_session(
        user_id=session.user_id,
        task_type=session.task_type,
        initial_context=session.initial_context
    )
    return {"coordination_uuid": coordination_uuid}

@router.post("/coordination/sessions/{coordination_uuid}/assign", response_model=dict)
async def assign_task_to_agent(
    coordination_uuid: str,
    assignment: TaskAssignment,
    db: AsyncSession = Depends(get_db),
    vector_db = Depends(get_vector_db)
):
    """Assign task to agent"""
    coordinator = AgentCoordinatorService(db, vector_db)
    success = await coordinator.assign_task_to_agent(
        coordination_uuid=coordination_uuid,
        agent_id=assignment.agent_id,
        task_details=assignment.task_details
    )
    return {"success": success}

@router.get("/coordination/agents/{user_id}", response_model=List[dict])
async def get_available_agents(
    user_id: int,
    capability: str = None,
    db: AsyncSession = Depends(get_db),
    vector_db = Depends(get_vector_db)
):
    """Get available agents for user"""
    coordinator = AgentCoordinatorService(db, vector_db)
    task_requirements = {"capability": capability} if capability else {}
    agents = await coordinator.get_available_agents(user_id, task_requirements)
    
    return [
        {
            "id": agent.id,
            "uuid": str(agent.uuid),
            "name": agent.name,
            "agent_type": agent.agent_type,
            "capabilities": agent.capabilities,
            "status": agent.status
        }
        for agent in agents
    ]

@router.post("/coordination/context", response_model=AgentContextResponse)
async def get_agent_context(
    context_request: AgentContextRequest,
    db: AsyncSession = Depends(get_db),
    vector_db = Depends(get_vector_db)
):
    """Get context for agent task"""
    coordinator = AgentCoordinatorService(db, vector_db)
    context = await coordinator.get_context_for_agent_task(
        user_id=context_request.user_id,
        current_prompt=context_request.current_prompt,
        agent_id=context_request.agent_id,
        context_window=context_request.context_window
    )
    return AgentContextResponse(**context)

# Conversation endpoints
@router.post("/conversations", response_model=dict)
async def store_user_conversation(
    user_id: int,
    conversation_text: str,
    conversation_type: str = "general",
    vector_db = Depends(get_vector_db)
):
    """Store user conversation"""
    conversation_service = UserConversationService(vector_db)
    conversation_uuid = await conversation_service.store_user_conversation(
        user_id=user_id,
        conversation_text=conversation_text,
        conversation_type=conversation_type
    )
    return {"conversation_uuid": conversation_uuid}

@router.get("/conversations/{user_id}", response_model=List[dict])
async def retrieve_user_conversations(
    user_id: int,
    query: str = None,
    limit: int = 10,
    conversation_type: str = None,
    vector_db = Depends(get_vector_db)
):
    """Retrieve user conversations"""
    conversation_service = UserConversationService(vector_db)
    return await conversation_service.retrieve_user_conversations(
        user_id=user_id,
        query=query,
        limit=limit,
        conversation_type=conversation_type
    )

@router.get("/conversations/{user_id}/history", response_model=List[dict])
async def get_conversation_history(
    user_id: int,
    vector_db = Depends(get_vector_db)
):
    """Get conversation history"""
    conversation_service = UserConversationService(vector_db)
    return await conversation_service.get_conversation_history(user_id)
