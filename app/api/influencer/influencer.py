from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy
import logging
import uuid

from app.api.auth import get_current_user
from app.api.influencer.influencer_models import InfluencerRead, InfluencerCreate, InfluencerUpdate, InfluencerSearchCriteria, InfluencerCreatePublic
from app.db.models import Influencer, User, Role, UserRole
from app.db.models.country import Country
from app.core.dependencies import require_role, require_any_role
from app.services.role_management import RoleManagementService
from app.db.session import get_db
from app.services.auth import hash_password
from app.core.rate_limiter import create_rate_limit_dependency
from typing import List

# Router for authenticated endpoints
router = APIRouter(dependencies=[Depends(get_current_user)])

# Router for unauthenticated endpoints
public_router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

@router.post("/create_influencer", response_model=InfluencerRead, status_code=status.HTTP_201_CREATED)
async def create_influencer(influencer_data: InfluencerCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    # Extract collaboration country IDs
    collaboration_ids = influencer_data.collaboration_country_ids
    create_data = influencer_data.dict(exclude={'collaboration_country_ids'})

    # Fetch country objects from the database
    if collaboration_ids:
        countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
        countries = countries_result.scalars().all()
        if len(countries) != len(collaboration_ids):
            raise HTTPException(status_code=400, detail="One or more collaboration countries not found.")
    else:
        countries = []

    # Create influencer instance
    new_influencer = Influencer(**create_data)
    new_influencer.collaboration_countries = countries
    
    db.add(new_influencer)
    try:
        await db.commit()
        await db.refresh(new_influencer)
        
        # Assign 'influencer' role to the user
        role_service = RoleManagementService(db)
        influencer_role_result = await db.execute(select(Role).where(Role.name == "influencer"))
        influencer_role = influencer_role_result.scalars().first()
        
        if influencer_role:
            await role_service.assign_role_to_user(current_user.id, influencer_role.id)
            logger.info(f"Assigned 'influencer' role to user {current_user.id}")
        else:
            logger.warning("'influencer' role not found in database")
        
        # Eagerly load relationships for the response
        result = await db.execute(
            select(Influencer)
            .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
            .where(Influencer.id == new_influencer.id)
        )
        return result.scalars().one()
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Data integrity error: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Create rate limiter for influencer creation
influencer_creation_rate_limit = create_rate_limit_dependency(
    max_requests=3,
    window_hours=1,
    error_message="You have exceeded the limit of 3 influencer profile creation requests per hour. Please try again later."
)

@public_router.post("/create_public", response_model=InfluencerRead, status_code=status.HTTP_201_CREATED)
async def create_influencer_public(
    request: Request,
    influencer_data: InfluencerCreatePublic, 
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(influencer_creation_rate_limit)
):
    """
    Create an influencer profile without authentication.
    Uses a single transaction for both user and influencer creation.
    Rate limited to 3 requests per hour per IP address.
    """
    try:
        # Check if username already exists
        existing_user = await db.execute(select(User).where(User.username == influencer_data.username))
        if existing_user.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="This username is already taken. Please choose a different username."
            )
        
        # Check if email already exists
        existing_email = await db.execute(select(User).where(User.email == influencer_data.email))
        if existing_email.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="This email address is already registered. Please use a different email or try logging in."
            )
        
        # Check if base country exists
        base_country_result = await db.execute(select(Country).where(Country.id == influencer_data.base_country_id))
        base_country = base_country_result.scalars().first()
        if not base_country:
            raise HTTPException(
                status_code=400, 
                detail="The selected base country is not valid. Please choose a valid country."
            )
        
        # Validate collaboration countries
        collaboration_ids = influencer_data.collaboration_country_ids
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
            if influencer_data.base_country_id in collaboration_ids:
                raise HTTPException(
                    status_code=400,
                    detail="The base country should not be included in collaboration countries. Please remove it from the collaboration list."
                )
        else:
            found_countries = []
        
        # Create user (NOT committed yet)
        new_user = User(
            username=influencer_data.username,
            hashed_password=hash_password(str(uuid.uuid4())),
            first_name=influencer_data.first_name,
            last_name=influencer_data.last_name,
            email=influencer_data.email
        )
        db.add(new_user)
        
        # Prepare influencer data
        create_data = influencer_data.dict(exclude={'collaboration_country_ids', 'first_name', 'last_name', 'username', 'email'})
        
        # ✅ COMMIT USER FIRST - Get the user ID
        await db.commit()
        await db.refresh(new_user)
        
        try:
            # Create influencer with the user's ID (now available)
            new_influencer = Influencer(**create_data, user_id=new_user.id)
            new_influencer.collaboration_countries = found_countries
            db.add(new_influencer)
            
            # ✅ COMMIT INFLUENCER - Save the influencer
            await db.commit()
            await db.refresh(new_influencer)
            
            # Assign 'influencer' role to the newly created user
            role_service = RoleManagementService(db)
            influencer_role_result = await db.execute(select(Role).where(Role.name == "influencer"))
            influencer_role = influencer_role_result.scalars().first()
            
            if influencer_role:
                await role_service.assign_role_to_user(new_user.id, influencer_role.id)
                logger.info(f"Assigned 'influencer' role to new user {new_user.id}")
            else:
                logger.warning("'influencer' role not found in database")
            
        except Exception as influencer_error:
            # ❌ INFLUENCER CREATION FAILED - Roll back user creation
            logger.error(f"Influencer creation failed after user creation: {str(influencer_error)}")
            
            # Delete the orphaned user
            await db.delete(new_user)
            await db.commit()
            
            # Re-raise the original error for proper handling
            raise influencer_error
        
        # Return the influencer with all relationships loaded
        result = await db.execute(
            select(Influencer)
            .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
            .where(Influencer.id == new_influencer.id)
        )
        return result.scalars().one()
        
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()  # ✅ ROLLBACK - Both user and influencer are undone
        
        # Parse the integrity error to provide human-readable messages
        error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
        # Log the detailed error for debugging
        logger.error(f"Database integrity error during influencer creation: {error_detail}")
        
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
        elif "influencers_user_id_fkey" in error_detail:
            raise HTTPException(
                status_code=400, 
                detail="Invalid user reference. Please try again."
            )
        elif "influencers_base_country_id_fkey" in error_detail:
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
        logger.error(f"Unexpected error during influencer creation: {str(e)}")
        logger.error(f"General Exception caught: {type(e)} - {str(e)}")
        logger.error(f"Exception class: {e.__class__.__name__}")
        logger.error(f"Exception module: {e.__class__.__module__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Exception args: {e.args}")
        
        # Create dynamic detail variable
        detail = "An unexpected error occurred while creating your influencer profile. Please try again later."
        if hasattr(e, 'detail'):
            # This is an HTTPException or similar
            logger.error(f"Exception detail: {e.detail}")
            detail = f"An unexpected error occurred while creating your influencer profile. Error: {e.detail}"
        elif hasattr(e, 'status_code'):
            # This has a status code
            logger.error(f"Exception status code: {e.status_code}")
        
        await db.rollback()  # ✅ ROLLBACK - Both user and influencer are undone
        raise HTTPException(
            status_code=500, 
            detail=detail
        )


@router.get("/get_influencer/{influencer_id}", response_model=InfluencerRead)
async def get_influencer_by_id(influencer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Influencer)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
        .where(Influencer.id == influencer_id)
    )
    influencer = result.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return influencer


@router.put("/update_influencer/{influencer_id}", response_model=InfluencerRead, dependencies=[Depends(require_role("admin"))])
async def update_influencer(influencer_id: int, influencer_data: InfluencerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Influencer).where(Influencer.id == influencer_id))
    influencer = result.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    update_data = influencer_data.dict(exclude_unset=True)
    
    if 'collaboration_country_ids' in update_data:
        collaboration_ids = update_data.pop('collaboration_country_ids')
        if collaboration_ids:
            countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
            influencer.collaboration_countries = countries_result.scalars().all()
        else:
            influencer.collaboration_countries = []

    for key, value in update_data.items():
        setattr(influencer, key, value)

    await db.commit()
    await db.refresh(influencer)
    
    # Eagerly load relationships for the response
    final_result = await db.execute(
        select(Influencer)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
        .where(Influencer.id == influencer.id)
    )
    return final_result.scalars().one()


@router.delete("/remove_influencer/{influencer_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
async def delete_influencer(influencer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Influencer).where(Influencer.id == influencer_id))
    influencer = result.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    await db.delete(influencer)
    await db.commit()


@router.get("/list", response_model=List[InfluencerRead])
async def list_influencers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Influencer)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_base_country", response_model=List[InfluencerRead])
async def search_by_base_country(country_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Influencer)
        .where(Influencer.base_country_id == country_id)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_collaboration_country", response_model=List[InfluencerRead])
async def search_by_collaboration_country(country_id: int, db: AsyncSession = Depends(get_db)):
    # Find influencers who are open to collaboration in the specified country OR are available globally.
    # The subquery finds influencers who have at least one entry in the collaboration table.
    subquery = select(Influencer.id).join(Influencer.collaboration_countries).distinct()
    
    result = await db.execute(
        select(Influencer)
        .where(
            sqlalchemy.or_(
                # Condition 1: They have the specific country in their list
                Influencer.collaboration_countries.any(Country.id == country_id),
                # Condition 2: They have NO entries in the collaboration list (they are global)
                sqlalchemy.not_(Influencer.id.in_(subquery))
            )
        )
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
    )
    return result.scalars().all()


@public_router.post("/search/by_criteria", response_model=List[InfluencerRead])
async def search_influencers_by_criteria(criteria: InfluencerSearchCriteria, db: AsyncSession = Depends(get_db)):
    """
    Search influencers by multiple criteria including countries, industry, and social media platform.
    This is an unauthenticated endpoint for public search functionality.
    """
    # Build the base query
    query = select(Influencer).options(
        selectinload(Influencer.user), 
        selectinload(Influencer.base_country), 
        selectinload(Influencer.collaboration_countries)
    )
    
    # Add country filter - search for influencers who are available in any of the specified countries
    if criteria.country_ids:
        # Subquery to find influencers who have at least one collaboration country
        subquery = select(Influencer.id).join(Influencer.collaboration_countries).distinct()
        
        query = query.where(
            sqlalchemy.or_(
                # Condition 1: They have any of the specified countries in their collaboration list
                Influencer.collaboration_countries.any(Country.id.in_(criteria.country_ids)),
                # Condition 2: They have NO entries in the collaboration list (they are global)
                sqlalchemy.not_(Influencer.id.in_(subquery))
            )
        )
    
    # Add industry filter (if we had industry data in the influencer model)
    # For now, we'll skip industry filtering as it's not in the current model
    
    # Add social media platform filter (if we had platform data in the influencer model)
    # For now, we'll skip platform filtering as it's not in the current model
    
    # Add availability filter - only show available influencers
    query = query.where(Influencer.availability == True)
    
    # Execute the query
    result = await db.execute(query)
    influencers = result.scalars().all()
    
    return influencers

