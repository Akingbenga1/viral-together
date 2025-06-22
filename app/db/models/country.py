from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, func
from app.db.base import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(2), nullable=False, unique=True, index=True, comment="ISO 3166-1 alpha-2 country code")
    code3 = Column(String(3), unique=True, comment="ISO 3166-1 alpha-3 country code")
    numeric_code = Column(String(3), comment="ISO 3166-1 numeric country code")
    phone_code = Column(String(10), comment="International dialing code")
    capital = Column(String(100))
    currency = Column(String(3), comment="ISO 4217 currency code")
    currency_name = Column(String(50))
    currency_symbol = Column(String(10))
    tld = Column(String(10), comment="Top-level domain")
    region = Column(String(50), index=True)
    timezones = Column(Text, comment="JSON array of timezones")
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now()) 