from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class DocumentTemplate(Base):
    __tablename__ = 'document_templates'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    subtype = Column(String(50))
    prompt_text = Column(Text, nullable=False)
    default_parameters = Column(JSON)
    file_format = Column(String(20), default='pdf', nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True) 