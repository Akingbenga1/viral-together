from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base
from app.db.models.user_role import UserRole
from app.db.models.role import Role

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    first_name = Column(String, unique=False, index=True)
    last_name = Column(String, unique=False, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile_number = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    stripe_customer_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    roles = relationship("Role", secondary=UserRole.__table__, backref="users")
    
    # AI Agent relationships
    agent_associations = relationship("UserAgentAssociation", back_populates="user", foreign_keys="UserAgentAssociation.user_id")
    
    # Recommendations relationship
    recommendations = relationship("InfluencerRecommendations", back_populates="user")
    
    # Influencer targets relationship
    influencer_targets = relationship("InfluencersTargets", back_populates="user")
    
