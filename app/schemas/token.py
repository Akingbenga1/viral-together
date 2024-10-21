from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str

# Model for token payload (useful for validating JWT)
class TokenData(BaseModel):
    username: Optional[str] = None