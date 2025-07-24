from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class GeneratedDocument(Base):
    __tablename__ = 'generated_documents'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    template_id = Column(Integer, ForeignKey('document_templates.id'), nullable=True)  # Made nullable for development
    type = Column(String(50), nullable=False, default='custom')  # Default for templateless docs
    subtype = Column(String(50), default='generated')  # Default subtype
    influencer_id = Column(Integer, ForeignKey('influencers.id'))
    business_id = Column(Integer, ForeignKey('businesses.id'))
    promotion_id = Column(Integer, ForeignKey('promotions.id'))
    collaboration_id = Column(Integer, ForeignKey('collaborations.id'))
    parameters = Column(JSON, nullable=False, default='{}')  # Default empty JSON
    file_path = Column(String(255), nullable=False)
    generation_status = Column(String(20), default='pending', nullable=False)
    error_message = Column(Text)
    generated_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 