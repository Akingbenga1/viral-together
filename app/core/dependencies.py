from fastapi import Depends, HTTPException, status
from app.api.auth import get_current_user
from app.schemas.user import UserRead
from typing import List
from app.db.session import get_db
from app.services.vector_db import VectorDatabaseService
from app.services.agent_coordinator_service import AgentCoordinatorService
from app.services.agent_response_service import AgentResponseService
from app.services.user_agent_association_service import UserAgentAssociationService
from app.services.user_conversation_service import UserConversationService

import logging

# Configure logging
logger = logging.getLogger(__name__)

# Define role hierarchy
# A higher number means more privileges
ROLE_HIERARCHY = {
    "user": 1,
    "influencer": 2,
    "business": 2,
    "professional_influencer": 3,
    "business_influencer": 4,
    "moderator": 5,
    "admin": 6,
    "super_admin": 7
}

def get_role_level(user: UserRead) -> int:
    if not user.roles:
        return 0
    # Return the highest role level for the user
    return max(ROLE_HIERARCHY.get(role.name, 0) for role in user.roles)

def require_role(required_role: str):
    def role_checker(current_user: UserRead = Depends(get_current_user)):
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        user_level = get_role_level(current_user)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have sufficient permissions for this resource.",
            )
        return current_user
    return role_checker


# Vector database dependency
def get_vector_db() -> VectorDatabaseService:
    return VectorDatabaseService()


# AI Agent service dependencies
def get_agent_coordinator_service(db = Depends(get_db), vector_db = Depends(get_vector_db)) -> AgentCoordinatorService:
    return AgentCoordinatorService(db, vector_db)


def get_agent_response_service(db = Depends(get_db)) -> AgentResponseService:
    return AgentResponseService(db)


def get_user_agent_association_service(db = Depends(get_db)) -> UserAgentAssociationService:
    return UserAgentAssociationService(db)


def get_user_conversation_service(vector_db = Depends(get_vector_db)) -> UserConversationService:
    return UserConversationService(vector_db)


def require_any_role(required_roles: List[str]):
    """
    Dependency that checks if the current user has at least one of the
    required roles. This check is based on role name, not hierarchy.
    """
    def role_checker(current_user: UserRead = Depends(get_current_user)):
        logger.info("require_any_role current_user.roles =====> %s", current_user)
        logger.info("require_any_role required_roles =====> %s", required_roles)
        user_role_names = {role.name for role in current_user.roles}
        logger.info("require_any_role user_role_names =====> %s", user_role_names)
        if not user_role_names.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have the required permissions. Must have one of: {', '.join(required_roles)}",
            )
        return current_user
    return role_checker

 