from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, MetaData
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

metadata = MetaData()

class SocialMediaPlatform(Base):
    __tablename__ = "social_media_platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    icon_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # One to many relationship with rate cards
    rate_cards = relationship("RateCard", back_populates="platform")