import sys
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
import sqlalchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.api.auth import get_current_user
from app.api.rate_card.rate_card_models import (
    RateCardCreate, RateCardRead, RateCardUpdate, RateCardSummary, RateProposalCreate, RateProposalRead, RateProposalUpdate
)
from app.db.models.influencer import Influencer
from app.db.models.rate_card import RateCard
# from app.db.models.social_media_platform import SocialMediaPlatform
# from app.db.models import Influencer, Business
from app.db.models.social_media_platform import SocialMediaPlatform
from app.db.session import get_db
from app.schemas import User
# from app.db.models.rate_proposal import RateProposal

router = APIRouter(dependencies=[Depends(get_current_user)])

# 1. Create a Rate Card
@router.post("/create_rate_card", response_model=RateCardRead)
async def create_rate_card(
    rate_card: RateCardCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        influencer_query = await db.execute(
            select(Influencer).filter(Influencer.id == rate_card.influencer_id)
        )
        influencer = influencer_query.scalars().first()
        
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # Verify the current user owns this influencer profile
        if influencer.user_id != current_user.id:
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to create a rate card for this influencer"
            )
        
        # Check if a rate card for this content type already exists
        existing_query = await db.execute(
            select(RateCard).filter(
                RateCard.influencer_id == rate_card.influencer_id,
                RateCard.content_type == rate_card.content_type,
                RateCard.platform_id == rate_card.platform_id
            )
        )
        existing = existing_query.scalars().first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"A rate card for {rate_card.content_type} and platform {existing.platform.name} already exists for this influencer"
            )

        # Create new rate card
        new_rate_card = RateCard(**rate_card.dict())
        

        db.add(new_rate_card)
        await db.commit()
        # await db.refresh(new_rate_card)
        
        # Calculate total rate
        response = RateCardRead(**rate_card.dict())


        return response
    except sqlalchemy.exc.IntegrityError as e:
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Foreign key constraint failed")
        elif "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Unique constraint failed")
        else:
            raise HTTPException(status_code=400, detail="Duplicate entry found")
    except sqlalchemy.exc.OperationalError as e:
        raise HTTPException(status_code=503, detail="Database operation failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 2. Get Rate Card by ID
@router.get("/get_rate_card/{rate_card_id}", response_model=RateCardRead)
async def get_rate_card_by_id(
    rate_card_id: int, 
    db: AsyncSession = Depends(get_db)
):
    rate_card_query = await db.execute(
        select(RateCard).options(selectinload(RateCard.platforms)).filter(RateCard.id == rate_card_id)
    )
    rate_card = rate_card_query.scalars().first()
    
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    # Calculate total rate
    response = RateCardRead(
        **{k: getattr(rate_card, k) for k in rate_card.__dict__ if not k.startswith('_')},
        total_rate=rate_card.calculate_total_rate(),
        platform=rate_card.platform
    )
    
    return response

# 3. Get All Rate Cards for an Influencer
@router.get("/influencer/{influencer_id}/rate_cards", response_model=List[RateCardRead])
async def get_influencer_rate_cards(
    influencer_id: int, 
    db: Session = Depends(get_db)
):
    # Verify influencer exists
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    # Get all rate cards with platform
    rate_cards_query = await db.execute(
        select(RateCard).options(selectinload(RateCard.platform)).filter(RateCard.influencer_id == influencer_id)
    )
    rate_cards = rate_cards_query.scalars().all()
    
    # Calculate total rates for each card
    response = []
    for card in rate_cards:
        response.append(
            RateCardRead(
                **{k: getattr(card, k) for k in card.__dict__ if not k.startswith('_')},
                total_rate=card.calculate_total_rate(),
                platform=card.platform
            )
        )
    
    return response

# 4. Update a Rate Card
@router.put("/update_rate_card/{rate_card_id}", response_model=RateCardRead)
async def update_rate_card(
    rate_card_id: int, 
    rate_card_data: RateCardUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the rate card with platform
    rate_card_query = await db.execute(
        select(RateCard).options(selectinload(RateCard.platforms)).filter(RateCard.id == rate_card_id)
    )
    rate_card = rate_card_query.scalars().first()
    
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    # Get the influencer to verify ownership
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == rate_card.influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    # Verify the current user owns this influencer profile
    if influencer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this rate card"
        )
    
    # Update platform if platform_id is provided
    if rate_card_data.platform_id is not None:
        platform_query = await db.execute(
            select(SocialMediaPlatform).filter(SocialMediaPlatform.id == rate_card_data.platform_id)
        )
        platform = platform_query.scalars().first()
        
        if not platform:
            raise HTTPException(
                status_code=404,
                detail="Social media platform not found"
            )
        
        rate_card.platform_id = rate_card_data.platform_id
    
    # Update rate card fields (excluding platform_id)
    update_data = rate_card_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key != 'platform_id':  # We already handled platform_id above
            setattr(rate_card, key, value)
    
    await db.commit()
    await db.refresh(rate_card)
    
    # Calculate total rate
    response = RateCardRead(
        **{k: getattr(rate_card, k) for k in rate_card.__dict__ if not k.startswith('_')},
        total_rate=rate_card.calculate_total_rate(),
        platform=rate_card.platform
    )
    
    return response

# 5. Delete a Rate Card
@router.delete("/delete_rate_card/{rate_card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_card(
    rate_card_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the rate card
    rate_card_query = await db.execute(
        select(RateCard).filter(RateCard.id == rate_card_id)
    )
    rate_card = rate_card_query.scalars().first()
    
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    # Get the influencer to verify ownership
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == rate_card.influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    # Verify the current user owns this influencer profile
    if influencer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to delete this rate card"
        )
    
    # Delete the rate card
    await db.delete(rate_card)
    await db.commit()
    
    return

# 6. Get Rate Card Summary for an Influencer
@router.get("/influencer/{influencer_id}/rate_summary", response_model=RateCardSummary)
async def get_rate_card_summary(
    influencer_id: int, 
    db: Session = Depends(get_db)
):
    # Verify influencer exists
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    # Get all rate cards
    rate_cards_query = await db.execute(
        select(RateCard).filter(RateCard.influencer_id == influencer_id)
    )
    rate_cards = rate_cards_query.scalars().all()
    
    if not rate_cards:
        raise HTTPException(
            status_code=404, 
            detail="No rate cards found for this influencer"
        )
    
    # Calculate summary statistics
    content_types = [card.content_type for card in rate_cards]
    total_rates = [card.calculate_total_rate() for card in rate_cards]
    
    summary = RateCardSummary(
        influencer_id=influencer_id,
        content_types=content_types,
        min_rate=min(total_rates),
        max_rate=max(total_rates),
        avg_rate=sum(total_rates) / len(total_rates)
    )
    
    return summary

# 7. Search Rate Cards by Price Range
@router.get("/search_rate_cards/{min_rate}/{max_rate}", response_model=List[RateCardRead])
async def search_rate_cards_by_price(
    min_rate: float,
    max_rate: float,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if max_rate < min_rate:
        raise HTTPException(
            status_code=400, 
            detail="Maximum rate cannot be lower than minimum rate"
        )
    
    # Build the query
    query = select(RateCard)
    
    # Apply content type filter if provided
    if content_type:
        query = query.filter(RateCard.content_type == content_type)
    
    # Execute the query
    rate_cards_query = await db.execute(query)
    rate_cards = rate_cards_query.scalars().all()
    
    # Filter by calculated total rate
    filtered_cards = []
    for card in rate_cards:
        total_rate = card.calculate_total_rate()
        if min_rate <= total_rate <= max_rate:
            filtered_cards.append(
                RateCardRead(
                    **{k: getattr(card, k) for k in card.__dict__ if not k.startswith('_')},
                    total_rate=total_rate
                )
            )
    
    return filtered_cards

# 8. New endpoint: Get Rate Cards by Platform
@router.get("/platform/{platform_id}/rate_cards", response_model=List[RateCardRead])
async def get_rate_cards_by_platform(
    platform_id: int,
    db: Session = Depends(get_db)
):
    # Verify platform exists
    platform_query = await db.execute(
        select(SocialMediaPlatform).filter(SocialMediaPlatform.id == platform_id)
    )
    platform = platform_query.scalars().first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Social media platform not found")
    
    # Get all rate cards for this platform
    rate_cards_query = await db.execute(
        select(RateCard)
        .options(selectinload(RateCard.platform))
        .join(RateCard.platform)
        .filter(SocialMediaPlatform.id == platform_id)
    )
    rate_cards = rate_cards_query.scalars().all()
    
    # Calculate total rates for each card
    response = []
    for card in rate_cards:
        response.append(
            RateCardRead(
                **{k: getattr(card, k) for k in card.__dict__ if not k.startswith('_')},
                total_rate=card.calculate_total_rate(),
                platform=card.platform
            )
        )
    
    return response

# 9. Create a Rate Proposal
@router.post("/create_rate_proposal", response_model=RateProposalRead)
async def create_rate_proposal(
    proposal: RateProposalCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify influencer exists
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == proposal.influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    # Verify the current user owns this influencer profile
    if influencer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to create a proposal for this influencer"
        )
    
    # Verify the business exists
    business_query = await db.execute(
        select(Business).filter(Business.id == proposal.business_id)
    )
    business = business_query.scalars().first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Verify the platform exists
    platform_query = await db.execute(
        select(SocialMediaPlatform).filter(SocialMediaPlatform.id == proposal.platform_id)
    )
    platform = platform_query.scalars().first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    # Create new rate proposal
    new_proposal = RateProposal(**proposal.dict())
    
    db.add(new_proposal)
    await db.commit()
    await db.refresh(new_proposal)
    
    return new_proposal
# 10. Get Rate Proposal by ID
@router.get("/rate_proposal/{proposal_id}", response_model=RateProposalRead)
async def get_rate_proposal_by_id(
    proposal_id: int,
    db: Session = Depends(get_db)
):
    proposal_query = await db.execute(
        select(RateProposal).filter(RateProposal.id == proposal_id)
    )
    proposal = proposal_query.scalars().first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Rate proposal not found")
    
    return proposal

# 11. Update Rate Proposal Status
@router.put("/rate_proposal/{proposal_id}", response_model=RateProposalRead)
async def update_rate_proposal(
    proposal_id: int,
    proposal_data: RateProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the proposal
    proposal_query = await db.execute(
        select(RateProposal).filter(RateProposal.id == proposal_id)
    )
    proposal = proposal_query.scalars().first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Rate proposal not found")
    
    # Get the influencer to verify ownership
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == proposal.influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    # Verify the current user owns this influencer profile
    if influencer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this proposal"
        )
    
    # Update proposal fields
    for key, value in proposal_data.dict(exclude_unset=True).items():
        setattr(proposal, key, value)
    
    await db.commit()
    await db.refresh(proposal)
    
    return proposal

# 12. Delete Rate Proposal
@router.delete("/rate_proposal/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the proposal
    proposal_query = await db.execute(
        select(RateProposal).filter(RateProposal.id == proposal_id)
    )
    proposal = proposal_query.scalars().first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Rate proposal not found")
    
    # Get the influencer to verify ownership
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == proposal.influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    # Verify the current user owns this influencer profile
    if influencer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to delete this proposal"
        )
    
    # Delete the proposal
    await db.delete(proposal)
    await db.commit()
    
    return

# 13. List Rate Proposals by Influencer
@router.get("/influencer/{influencer_id}/rate_proposals", response_model=List[RateProposalRead])
async def get_influencer_rate_proposals(
    influencer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify influencer exists
    influencer_query = await db.execute(
        select(Influencer).filter(Influencer.id == influencer_id)
    )
    influencer = influencer_query.scalars().first()
    
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    # Verify the current user owns this influencer profile
    if influencer.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view proposals for this influencer"
        )
    
    # Get all proposals for this influencer
    proposals_query = await db.execute(
        select(RateProposal).filter(RateProposal.influencer_id == influencer_id)
    )
    proposals = proposals_query.scalars().all()
    
    return proposals

# 14. List Rate Proposals by Business
@router.get("/business/{business_id}/rate_proposals", response_model=List[RateProposalRead])
async def get_business_rate_proposals(
    business_id: int,
    db: Session = Depends(get_db)
):
    # Verify business exists
    business_query = await db.execute(
        select(Business).filter(Business.id == business_id)
    )
    business = business_query.scalars().first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Get all proposals for this business
    proposals_query = await db.execute(
        select(RateProposal).filter(RateProposal.business_id == business_id)
    )
    proposals = proposals_query.scalars().all()
    
    return proposals 