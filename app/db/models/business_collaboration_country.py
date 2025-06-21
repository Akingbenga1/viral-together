from sqlalchemy import Column, Integer, ForeignKey, Table
from app.db.base import Base

business_collaboration_countries = Table(
    "business_collaboration_countries",
    Base.metadata,
    Column("business_id", Integer, ForeignKey("businesses.id"), primary_key=True),
    Column("country_id", Integer, ForeignKey("countries.id"), primary_key=True),
) 