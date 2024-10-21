import sqlalchemy
from sqlalchemy.orm import as_declarative

@as_declarative()
class Base:
    metadata = None
