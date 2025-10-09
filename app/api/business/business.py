from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, or_, not_, func, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy
import logging
import uuid
from typing import List, Dict, Any

from app.api.auth import get_current_user_dependency
from app.api.business.business_models import BusinessRead, BusinessCreate, BusinessUpdate, BusinessCreatePublic
from app.db.models import Business, User, Role, UserRole
from app.db.models.country import Country
from app.core.dependencies import require_role, require_any_role
from app.db.session import get_db
from app.services.auth import hash_password
from app.services.role_management import RoleManagementService
from app.core.rate_limiter import business_creation_rate_limit

# Configure logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user_dependency)])

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
    
    Requirements:
    - business_location is required
    - desired_influencer_location is optional
    - Password is optional (auto-generated if not provided)
    - User is automatically assigned the 'business' role
    """
    from app.db.models.location import BusinessOperationalLocation
    
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
        
        # Handle password: use provided password or generate one
        if business_data.password:
            hashed_password = hash_password(business_data.password)
        else:
            hashed_password = hash_password(str(uuid.uuid4()))
        
        # Create user (NOT committed yet)
        new_user = User(
            username=business_data.username,
            hashed_password=hashed_password,
            first_name=business_data.first_name,
            last_name=business_data.last_name,
            email=business_data.contact_email
        )
        db.add(new_user)
        # ❌ NO COMMIT HERE - Keep in same transaction
        
        # Prepare business data (exclude user fields, password, and location fields)
        create_data = business_data.dict(exclude={
            'collaboration_country_ids', 'first_name', 'last_name', 'username', 
            'password', 'business_location', 'desired_influencer_location'
        })
        
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
            
            logger.info(f"Business created successfully with ID: {new_business.id}")
            
            # Save business location (required, is_primary=True)
            logger.info("Starting location data save...")
            business_loc = business_data.business_location
            business_location = BusinessOperationalLocation(
                business_id=new_business.id,
                city_name=business_loc.city_name or "Unknown",
                region_name=business_loc.region_name,
                region_code=business_loc.region_code,
                country_code=business_loc.country_code or "XX",
                country_name=business_loc.country_name or "Unknown",
                latitude=business_loc.latitude,
                longitude=business_loc.longitude,
                is_primary=True
            )
            db.add(business_location)
            
            # Save desired influencer location if provided (optional, is_primary=False)
            if business_data.desired_influencer_location:
                desired_loc = business_data.desired_influencer_location
                desired_influencer_location = BusinessOperationalLocation(
                    business_id=new_business.id,
                    city_name=desired_loc.city_name or "Unknown",
                    region_name=desired_loc.region_name,
                    region_code=desired_loc.region_code,
                    country_code=desired_loc.country_code or "XX",
                    country_name=desired_loc.country_name or "Unknown",
                    latitude=desired_loc.latitude,
                    longitude=desired_loc.longitude,
                    is_primary=False
                )
                db.add(desired_influencer_location)
            
            # Commit all location data
            await db.commit()
            logger.info("Location data committed successfully")
            
            # Assign 'business' role to the newly created user
            logger.info("Starting role assignment...")
            role_service = RoleManagementService(db)
            business_role_result = await db.execute(select(Role).where(Role.name == "business"))
            business_role = business_role_result.scalars().first()
            
            if business_role:
                await role_service.assign_role_to_user(new_user.id, business_role.id)
                logger.info(f"Assigned 'business' role to new user {new_user.id}")
            else:
                logger.warning("'business' role not found in database")
            
        except Exception as business_error:
            # ❌ BUSINESS CREATION FAILED - Roll back user creation
            logger.error(f"Business creation failed after user creation: {str(business_error)}")
            logger.error(f"Error type: {type(business_error)}")
            logger.error(f"Error details: {business_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
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
    try:
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
        
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()
        error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Database integrity error during business update: {error_detail}")
        
        if "businesses_name_key" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="A business with this name already exists. Please choose a different business name."
            )
        elif "businesses_base_country_id_fkey" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="The selected base country is not valid. Please choose a valid country."
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="The provided data conflicts with existing records. Please check your information and try again."
            )
            
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during business update: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while updating the business. Please try again later."
        )


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


@public_router.post("/promotions-with-collaborations")
async def get_business_promotions_with_collaboration_stats(
    request: dict,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get all promotions for all businesses owned by a user with aggregated collaboration statistics.
    Returns promotions ordered by ID with counts of active, pending, and total influencers.
    Optimized single-query approach using SQL aggregation.
    
    Request body: { "business_owner_id": int }
    """
    from app.db.models.promotions import Promotion
    from app.db.models.collaborations import Collaboration
    
    business_owner_id = request.get("business_owner_id")
    
    if not business_owner_id:
        raise HTTPException(status_code=400, detail="business_owner_id is required")
    
    # Get all businesses owned by this user
    businesses_result = await db.execute(
        select(Business.id).where(Business.owner_id == business_owner_id)
    )
    business_ids = [row[0] for row in businesses_result.all()]
    
    if not business_ids:
        logger.info(f"No businesses found for owner_id {business_owner_id}")
        return JSONResponse(content=[])
    
    logger.info(f"Found {len(business_ids)} businesses for owner_id {business_owner_id}: {business_ids}")
    
    # Build query with aggregated collaboration stats for ALL businesses owned by the user
    # Use LEFT JOIN and conditional aggregation to count collaborations by status
    query = (
        select(
            Promotion.id,
            Promotion.uuid,
            Promotion.business_id,
            Promotion.promotion_name,
            Promotion.promotion_item,
            Promotion.description,
            Promotion.start_date,
            Promotion.end_date,
            Promotion.discount,
            Promotion.budget,
            Promotion.spent_amount,
            Promotion.status,
            Promotion.target_audience,
            Promotion.social_media_platform_id,
            Promotion.created_at,
            Promotion.updated_at,
            func.count(Collaboration.id).label('total_collaborations'),
            func.sum(case((Collaboration.status == 'active', 1), else_=0)).label('active_count'),
            func.sum(case((Collaboration.status == 'approved', 1), else_=0)).label('approved_count'),
            func.sum(case((Collaboration.status == 'pending', 1), else_=0)).label('pending_count'),
            func.sum(case((Collaboration.status == 'rejected', 1), else_=0)).label('rejected_count')
        )
        .outerjoin(Collaboration, Promotion.id == Collaboration.promotion_id)
        .where(Promotion.business_id.in_(business_ids))
        .group_by(Promotion.id)
        .order_by(Promotion.id.desc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Transform results into structured response
    promotions = []
    for row in rows:
        promotions.append({
            "id": row.id,
            "uuid": str(row.uuid) if row.uuid else None,
            "business_id": row.business_id,
            "promotion_name": row.promotion_name,
            "promotion_item": row.promotion_item,
            "description": row.description,
            "start_date": row.start_date.isoformat() if row.start_date else None,
            "end_date": row.end_date.isoformat() if row.end_date else None,
            "discount": float(row.discount) if row.discount else None,
            "budget": float(row.budget) if row.budget else None,
            "spent_amount": float(row.spent_amount) if row.spent_amount else 0,
            "status": row.status,
            "target_audience": row.target_audience,
            "social_media_platform_id": row.social_media_platform_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "collaboration_stats": {
                "total": int(row.total_collaborations or 0),
                "active": int(row.active_count or 0),
                "approved": int(row.approved_count or 0),
                "pending": int(row.pending_count or 0),
                "rejected": int(row.rejected_count or 0)
            }
        })
    
    logger.info(f"Fetched {len(promotions)} promotions with collaboration stats for owner {business_owner_id} across {len(business_ids)} businesses")
    
    return JSONResponse(content=promotions)
