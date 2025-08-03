from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, or_, not_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy
import logging
import uuid
from typing import List

from app.api.auth import get_current_user
from app.api.business.business_models import BusinessRead, BusinessCreate, BusinessUpdate, BusinessCreatePublic
from app.db.models import Business, User
from app.db.models.country import Country
from app.core.dependencies import require_role, require_any_role
from app.db.session import get_db
from app.services.auth import hash_password
from app.core.rate_limiter import business_creation_rate_limit

# Configure logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])

# Public router for unauthenticated endpoints
public_router = APIRouter()

@public_router.post("/create_public", response_model=BusinessRead, status_code=status.HTTP_201_CREATED)
async def create_business_public(
    request: Request,
    business_data: BusinessCreatePublic, 
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(business_creation_rate_limit)
):
    """
    Create a business profile without authentication.
    Uses a single transaction for both user and business creation.
    Rate limited to 3 requests per hour per IP address.
    """
    try:
        # Check if username already exists
        existing_user = await db.execute(select(User).where(User.username == business_data.username))
        if existing_user.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="This username is already taken. Please choose a different username."
            )
        
        # Check if email already exists
        existing_email = await db.execute(select(User).where(User.email == business_data.contact_email))
        if existing_email.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="This email address is already registered. Please use a different email or try logging in."
            )
        
        # Check if business name already exists
        existing_business = await db.execute(select(Business).where(Business.name == business_data.name))
        if existing_business.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="A business with this name already exists. Please choose a different business name."
            )
        
        # Check if base country exists
        base_country_result = await db.execute(select(Country).where(Country.id == business_data.base_country_id))
        base_country = base_country_result.scalars().first()
        if not base_country:
            raise HTTPException(
                status_code=400, 
                detail="The selected base country is not valid. Please choose a valid country."
            )
        
        # Validate collaboration countries
        collaboration_ids = business_data.collaboration_country_ids
        if collaboration_ids:
            countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
            found_countries = countries_result.scalars().all()
            if len(found_countries) != len(collaboration_ids):
                # Find which countries are missing
                found_ids = {country.id for country in found_countries}
                missing_ids = set(collaboration_ids) - found_ids
                raise HTTPException(
                    status_code=400, 
                    detail=f"One or more selected collaboration countries are not valid. Invalid country IDs: {list(missing_ids)}"
                )
            
            # Check if base country is in collaboration countries (optional validation)
            if business_data.base_country_id in collaboration_ids:
                raise HTTPException(
                    status_code=400,
                    detail="The base country should not be included in collaboration countries. Please remove it from the collaboration list."
                )
        else:
            found_countries = []
        
        # ✅ NO COMMIT YET - Everything stays in the same transaction
        
        # Create user (NOT committed yet)
        new_user = User(
            username=business_data.username,
            hashed_password=hash_password(str(uuid.uuid4())),
            first_name=business_data.first_name,
            last_name=business_data.last_name,
            email=business_data.contact_email
        )
        db.add(new_user)
        # ❌ NO COMMIT HERE - Keep in same transaction
        
        # Prepare business data
        create_data = business_data.dict(exclude={'collaboration_country_ids', 'first_name', 'last_name', 'username'})
        
        # ✅ COMMIT USER FIRST - Get the user ID
        await db.commit()
        await db.refresh(new_user)
        
        try:
            # Create business with the user's ID (now available)
            new_business = Business(**create_data, owner_id=new_user.id)
            new_business.collaboration_countries = found_countries
            db.add(new_business)
            
            # ✅ COMMIT BUSINESS - Save the business
            await db.commit()
            await db.refresh(new_business)
            
        except Exception as business_error:
            # ❌ BUSINESS CREATION FAILED - Roll back user creation
            logger.error(f"Business creation failed after user creation: {str(business_error)}")
            
            # Delete the orphaned user
            await db.delete(new_user)
            await db.commit()
            
            # Re-raise the original error for proper handling
            raise business_error
        
        # Return the business with all relationships loaded
        result = await db.execute(
            select(Business)
            .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
            .where(Business.id == new_business.id)
        )
        return result.scalars().one()
        
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()  # ✅ ROLLBACK - Both user and business are undone
        
        # Parse the integrity error to provide human-readable messages
        error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
        # Log the detailed error for debugging
        logger.error(f"Database integrity error during business creation: {error_detail}")
        
        if "users_username_key" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="This username is already taken. Please choose a different username."
            )
        elif "users_email_key" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="This email address is already registered. Please use a different email or try logging in."
            )
        elif "businesses_name_key" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="A business with this name already exists. Please choose a different business name."
            )
        elif "users_mobile_number_key" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="This mobile number is already registered. Please use a different mobile number."
            )
        elif "users_stripe_customer_id_key" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="This Stripe customer ID is already in use. Please contact support."
            )
        elif "businesses_owner_id_fkey" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="Invalid user reference. Please try again."
            )
        elif "businesses_base_country_id_fkey" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="The selected base country is not valid. Please choose a valid country."
            )
        else:
            # Generic integrity error message
            raise HTTPException(
                status_code=400, 
                detail="The provided data conflicts with existing records. Please check your information and try again."
            )
            
    except sqlalchemy.exc.DataError as e:
        await db.rollback()
        error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        if "value too long" in error_detail.lower():
            raise HTTPException(
                status_code=400, 
                detail="One or more fields exceed the maximum allowed length. Please shorten your input."
            )
        elif "invalid input syntax" in error_detail.lower():
            raise HTTPException(
                status_code=400, 
                detail="Invalid data format provided. Please check your input and try again."
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid data format. Please check your input and try again."
            )
            
    except sqlalchemy.exc.ProgrammingError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="A system error occurred. Please try again later or contact support."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during business creation: {str(e)}")
        logger.error(f"General Exception caught: {type(e)} - {str(e)}")
        logger.error(f"Exception class: {e.__class__.__name__}")
        logger.error(f"Exception module: {e.__class__.__module__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Exception args: {e.args}")
        
        # Create dynamic detail variable
        detail = "An unexpected error occurred while creating your business profile. Please try again later."
        if hasattr(e, 'detail'):
            # This is an HTTPException or similar
            logger.error(f"Exception detail: {e.detail}")
            detail = f"An unexpected error occurred while creating your business profile. Error: {e.detail}"
        elif hasattr(e, 'status_code'):
            # This has a status code
            logger.error(f"Exception status code: {e.status_code}")
        
        await db.rollback()  # ✅ ROLLBACK - Both user and business are undone
        raise HTTPException(
            status_code=500, 
            detail=detail
        )

@router.post("/create", response_model=BusinessRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_any_role(["business", "admin", "super_admin"]))])
async def create_business(business_data: BusinessCreate, db: AsyncSession = Depends(get_db)):
    collaboration_ids = business_data.collaboration_country_ids
    create_data = business_data.dict(exclude={'collaboration_country_ids'})

    if collaboration_ids:
        countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
        countries = countries_result.scalars().all()
        if len(countries) != len(collaboration_ids):
            raise HTTPException(status_code=400, detail="One or more collaboration countries not found.")
    else:
        countries = []

    new_business = Business(**create_data)
    new_business.collaboration_countries = countries
    
    db.add(new_business)
    try:
        await db.commit()
        await db.refresh(new_business)
        result = await db.execute(
            select(Business)
            .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
            .where(Business.id == new_business.id)
        )
        return result.scalars().one()
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Data integrity error: {e.orig}")


@router.get("/get_business_by_id/{business_id}", response_model=BusinessRead)
async def get_business(business_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Business)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
        .where(Business.id == business_id)
    )
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.put("/{business_id}", response_model=BusinessRead, dependencies=[Depends(require_any_role(["admin", "super_admin"]))])
async def update_business(business_id: int, business_data: BusinessUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    update_data = business_data.dict(exclude_unset=True)
    
    if 'collaboration_country_ids' in update_data:
        collaboration_ids = update_data.pop('collaboration_country_ids')
        if collaboration_ids:
            countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
            business.collaboration_countries = countries_result.scalars().all()
        else:
            business.collaboration_countries = []

    for key, value in update_data.items():
        setattr(business, key, value)

    await db.commit()
    await db.refresh(business)
    
    final_result = await db.execute(
        select(Business)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
        .where(Business.id == business.id)
    )
    return final_result.scalars().one()


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_any_role(["admin", "super_admin"]))])
async def delete_business(business_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    await db.delete(business)
    await db.commit()


@router.get("/get_all", response_model=List[BusinessRead])
async def list_all_businesses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Business)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_base_country", response_model=List[BusinessRead])
async def search_by_base_country(country_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Business)
        .where(Business.base_country_id == country_id)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_collaboration_country", response_model=List[BusinessRead])
async def search_by_collaboration_country(country_id: int, db: AsyncSession = Depends(get_db)):
    subquery = select(Business.id).join(Business.collaboration_countries).distinct()
    
    result = await db.execute(
        select(Business)
        .where(
            or_(
                Business.collaboration_countries.any(Country.id == country_id),
                not_(Business.id.in_(subquery))
            )
        )
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
    )
    return result.scalars().all()
