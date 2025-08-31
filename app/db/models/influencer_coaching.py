from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, JSON, DECIMAL
from sqlalchemy.orm import relationship
from app.db.base import Base

class InfluencerCoachingGroup(Base):
    __tablename__ = "influencer_coaching_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    coach_influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)  # Only if is_paid is True
    currency = Column(String(3), default="USD", nullable=False)
    max_members = Column(Integer, nullable=True)  # NULL means unlimited
    current_members = Column(Integer, default=0, nullable=False)
    join_code = Column(String(20), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    coach = relationship("Influencer", foreign_keys=[coach_influencer_id], back_populates="coaching_groups")
    members = relationship("InfluencerCoachingMember", back_populates="group")

class InfluencerCoachingMember(Base):
    __tablename__ = "influencer_coaching_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("influencer_coaching_groups.id"), nullable=False)
    member_influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    payment_status = Column(String(20), default="pending", nullable=False)  # pending, paid, free
    payment_reference = Column(String(255), nullable=True)  # External payment reference
    
    # Relationships
    group = relationship("InfluencerCoachingGroup", back_populates="members")
    member = relationship("Influencer", foreign_keys=[member_influencer_id])

class InfluencerCoachingSession(Base):
    __tablename__ = "influencer_coaching_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("influencer_coaching_groups.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    session_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    meeting_link = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=True)
    materials = Column(JSON, nullable=True)  # Array of material URLs
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    group = relationship("InfluencerCoachingGroup")

class InfluencerCoachingMessage(Base):
    __tablename__ = "influencer_coaching_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("influencer_coaching_groups.id"), nullable=False)
    sender_influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)  # text, file, image, video
    file_url = Column(String(500), nullable=True)
    is_announcement = Column(Boolean, default=False, nullable=False)  # Only coach can make announcements
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    group = relationship("InfluencerCoachingGroup")
    sender = relationship("Influencer", foreign_keys=[sender_influencer_id])
