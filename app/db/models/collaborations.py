from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class Collaboration(Base):
    __tablename__ = 'collaborations'
    id = Column(Integer, primary_key=True)
    influencer_id = Column(Integer, ForeignKey('influencers.id'), nullable=False)
    promotion_id = Column(Integer, ForeignKey('promotions.id'), nullable=False)
    status = Column(String(50), default='pending')
    proposed_amount = Column(Numeric(10, 2))
    negotiated_amount = Column(Numeric(10, 2))
    negotiable = Column(Boolean, default=False)
    collaboration_type = Column(String(50), nullable=False)
    deliverables = Column(String)
    deadline = Column(DateTime)
    terms_and_conditions = Column(String)
    contract_signed = Column(Boolean, default=False)
    payment_status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime) 