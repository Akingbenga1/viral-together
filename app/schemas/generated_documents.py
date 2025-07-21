from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class GeneratedDocumentBase(BaseModel):
    user_id: int
    template_id: int
    type: str
    subtype: Optional[str]
    influencer_id: Optional[int]
    business_id: Optional[int]
    promotion_id: Optional[int]
    collaboration_id: Optional[int]
    parameters: Dict
    file_path: str
    generation_status: str = 'pending'
    error_message: Optional[str]
    generated_at: Optional[datetime]

class GeneratedDocumentCreate(GeneratedDocumentBase):
    pass

class GeneratedDocument(GeneratedDocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 