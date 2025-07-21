from sqlalchemy import Column, Integer, ForeignKey, Table
from app.db.base import metadata

collaboration_countries = Table(
    'collaboration_countries',
    metadata,
    Column('collaboration_id', Integer, ForeignKey('collaborations.id'), primary_key=True),
    Column('country_id', Integer, ForeignKey('countries.id'), primary_key=True),
) 