from sqlalchemy import Column, Integer, ForeignKey, Table
from app.db.base import Base

influencer_collaboration_countries = Table(
    "influencer_collaboration_countries",
    Base.metadata,
    Column("influencer_id", Integer, ForeignKey("influencers.id"), primary_key=True),
    Column("country_id", Integer, ForeignKey("countries.id"), primary_key=True),
) 