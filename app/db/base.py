import sqlalchemy
from sqlalchemy.orm import as_declarative
from sqlalchemy import MetaData

metadata = MetaData()

@as_declarative()
class Base:
    metadata = None