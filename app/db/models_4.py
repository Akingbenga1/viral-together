from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, unique=False, index=True)
    last_name = Column(String, unique=False, index=True)
    username = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, unique=False, index=True)
    hashed_password = Column(String)
