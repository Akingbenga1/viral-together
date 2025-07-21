from sqlalchemy import Column, Integer, DateTime, String, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class PromotionInterest(Base):
    __tablename__ = 'promotion_interest'
    id = Column(Integer, primary_key=True)
    promotion_id = Column(Integer, ForeignKey('promotions.id'), nullable=False)
    influencer_id = Column(Integer, ForeignKey('influencers.id'), nullable=False)
    expressed_interest = Column(DateTime, default=func.now())
    status = Column(String(50), default='pending')
    notes = Column(Text) 