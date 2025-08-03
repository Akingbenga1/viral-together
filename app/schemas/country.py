from pydantic import BaseModel
from typing import Optional, List

class CountryRead(BaseModel):
    id: int
    name: str
    code: str
    code3: Optional[str] = None
    numeric_code: Optional[str] = None
    phone_code: Optional[str] = None
    capital: Optional[str] = None
    currency: Optional[str] = None
    currency_name: Optional[str] = None
    currency_symbol: Optional[str] = None
    tld: Optional[str] = None
    region: Optional[str] = None
    timezones: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CountryList(BaseModel):
    countries: List[CountryRead] 