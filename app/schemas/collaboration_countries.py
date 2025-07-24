from pydantic import BaseModel

class CollaborationCountry(BaseModel):
    collaboration_id: int
    country_id: int

    class Config:
        from_attributes = True 