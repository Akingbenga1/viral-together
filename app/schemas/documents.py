from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class DocumentRequest(BaseModel):
    template_id: int
    user_id: int
    parameters: Dict
    influencer_id: Optional[int]
    business_id: Optional[int]
    promotion_id: Optional[int]
    collaboration_id: Optional[int]

class DocumentResponse(BaseModel):
    id: int
    file_url: str
    status: str 