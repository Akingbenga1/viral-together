from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class DocumentTemplateBase(BaseModel):
    name: str
    type: str
    subtype: Optional[str]
    prompt_text: str
    default_parameters: Optional[Dict]
    file_format: str = 'pdf'
    created_by: Optional[int]
    is_active: bool = True

class DocumentTemplateCreate(DocumentTemplateBase):
    pass

class DocumentTemplate(DocumentTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 