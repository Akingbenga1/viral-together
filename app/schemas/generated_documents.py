from pydantic import BaseModel, validator
from typing import Optional, Dict
from datetime import datetime

class GeneratedDocumentBase(BaseModel):
    user_id: int
    template_id: Optional[int] = None  # Made optional for development
    type: str = "custom"  # Default type when no template
    subtype: Optional[str] = "generated"  # Default subtype
    influencer_id: Optional[int] = None
    business_id: Optional[int] = None
    promotion_id: Optional[int] = None
    collaboration_id: Optional[int] = None
    parameters: Dict = {}  # Default empty dict
    file_path: Optional[str] = None  # Will be generated
    generation_status: str = 'pending'
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None

class GeneratedDocumentCreate(BaseModel):
    user_id: int
    template_id: Optional[int] = None  # Made optional for development
    influencer_id: Optional[int] = None
    business_id: Optional[int] = None
    promotion_id: Optional[int] = None
    collaboration_id: Optional[int] = None
    parameters: Dict = {}  # Default empty dict

    @validator('parameters', always=True)
    def validate_content_source(cls, v, values):
        """Ensure at least some content is provided when no template"""
        template_id = values.get('template_id')
        
        if not template_id and not v:
            raise ValueError('Either template_id or parameters with content must be provided')
        
        # If no template, ensure we have some content to work with
        if not template_id and 'content' not in v:
            v['content'] = 'Default document content generated without template'
            
        return v

class GeneratedDocument(GeneratedDocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 