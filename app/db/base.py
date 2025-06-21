import sqlalchemy
from sqlalchemy.orm import as_declarative
from sqlalchemy import MetaData
# removed model imports to prevent circular dependency

metadata = MetaData()

@as_declarative()
class Base:
    metadata = metadata