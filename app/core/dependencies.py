from fastapi import Depends, HTTPException, status
from app.api.auth import get_current_user
from app.schemas.user import UserRead

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