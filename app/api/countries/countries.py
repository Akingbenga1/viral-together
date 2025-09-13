from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from typing import Optional, List
from app.db.session import get_db
from app.db.models.country import Country
from app.schemas.country import CountryRead
from app.core.query_helpers import safe_scalar_one_or_none
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[CountryRead])
async def get_countries(
    search: Optional[str] = Query(None, description="Search countries by name"),
    region: Optional[str] = Query(None, description="Filter by region"),
    limit: int = Query(50, description="Limit results", ge=1, le=100),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get all countries with optional search and filtering"""
    
    try:
        # Build query
        query = select(Country)
        
        # Add search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    Country.name.ilike(search_term),
                    Country.code.ilike(search_term),
                    Country.code3.ilike(search_term) if Country.code3 else False
                )
            )
        
        # Add region filter
        if region:
            query = query.where(Country.region == region)
        
        # Add ordering and pagination
        query = query.order_by(Country.name).offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        countries = result.scalars().all()
        
        logger.info(f"Retrieved {len(countries)} countries (search: {search}, region: {region})")
        
        return countries
        
    except Exception as e:
        logger.error(f"Error retrieving countries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve countries")

@router.get("/regions", response_model=List[str])
async def get_regions(db: AsyncSession = Depends(get_db)):
    """Get all available regions"""
    
    try:
        query = select(Country.region).where(Country.region.isnot(None)).distinct()
        result = await db.execute(query)
        regions = [row[0] for row in result.fetchall()]
        
        logger.info(f"Retrieved {len(regions)} regions")
        
        return sorted(regions)
        
    except Exception as e:
        logger.error(f"Error retrieving regions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve regions")

@router.get("/{country_id}", response_model=CountryRead)
async def get_country(country_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific country by ID"""
    
    try:
        query = select(Country).where(Country.id == country_id)
        result = await db.execute(query)
        country = await safe_scalar_one_or_none(result)
        
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        
        return country
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving country {country_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve country") 