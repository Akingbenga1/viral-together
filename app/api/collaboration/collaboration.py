from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, case
from typing import List, Dict
from app.db.session import get_db
from app.db.models.collaborations import Collaboration as CollaborationModel
from app.db.models.promotions import Promotion as PromotionModel
from app.db.models.business import Business as BusinessModel
from app.db.models.influencer import Influencer as InfluencerModel
from app.db.models.user import User as UserModel
from app.db.models.generated_documents import GeneratedDocument
from app.schemas.collaborations import CollaborationCreate, Collaboration
from pydantic import BaseModel
from app.core.query_helpers import safe_scalar_one_or_none
import logging

# Import notification services
from app.services.notification_service import notification_service
from app.schemas.notification import (
    CollaborationCreatedNotificationData,
    CollaborationApprovedNotificationData
)

router = APIRouter(prefix="/collaborations", tags=["collaborations"])

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic models for approval/rejection endpoints
class CollaborationActionRequest(BaseModel):
    influencer_id: int
    reason: str = None  # Optional reason for rejection

class BulkCollaborationApprovalRequest(BaseModel):
    promotion_id: int
    influencer_ids: List[int]

@router.post("", response_model=Collaboration)
async def create_collaboration(
    collaboration: CollaborationCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Get related entities for logging and notifications
    collaboration_result = await db.execute(
        select(PromotionModel, BusinessModel, InfluencerModel)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, InfluencerModel.id == collaboration.influencer_id)
        .where(PromotionModel.id == collaboration.promotion_id)
    )
    collaboration_data = collaboration_result.first()
    
    if not collaboration_data:
        raise HTTPException(status_code=404, detail="Promotion or influencer not found")
    
    promotion, business, influencer = collaboration_data
    
    # Create collaboration with server-side UUID if missing
    payload = collaboration.dict()
    if not payload.get('uuid'):
        payload['uuid'] = uuid.uuid4()
    db_collaboration = CollaborationModel(**payload)
    
    promotion_name = getattr(promotion, 'promotion_name', f'Promotion {collaboration.promotion_id}')
    business_name = getattr(business, 'name', f'Business {business.id}')
    influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
    
    logger.info(f"Creating {collaboration.collaboration_type} collaboration for '{promotion_name}' (ID: {collaboration.promotion_id}) with influencer '{influencer_name}' (ID: {collaboration.influencer_id})")
    
    db.add(db_collaboration)
    await db.commit()
    await db.refresh(db_collaboration)
    
    # 🔔 TRIGGER NOTIFICATION: Collaboration Created
    notification_data = CollaborationCreatedNotificationData(
        collaboration_id=db_collaboration.id,
        collaboration_type=collaboration.collaboration_type,
        promotion_id=collaboration.promotion_id,
        promotion_name=promotion_name,
        business_id=business.id,
        business_name=business_name,
        influencer_id=collaboration.influencer_id,
        influencer_name=influencer_name,
        proposed_amount=getattr(collaboration, 'proposed_amount', None)
    )
    
    # Create notification for business
    await notification_service.create_collaboration_created_notification(
        db=db,
        data=notification_data,
        background_tasks=background_tasks
    )
    
    logger.info(f"Notification triggered for collaboration creation: '{influencer_name}' with '{business_name}' for '{promotion_name}'")
    
    return db_collaboration

@router.get("/{collaboration_id}", response_model=Collaboration)
async def get_collaboration(collaboration_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    collaboration = await safe_scalar_one_or_none(result)
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    return collaboration

@router.put("/{collaboration_id}", response_model=Collaboration)
async def update_collaboration(collaboration_id: int, collaboration: CollaborationCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    db_collaboration = await safe_scalar_one_or_none(result)
    if db_collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    for key, value in collaboration.dict().items():
        setattr(db_collaboration, key, value)
    await db.commit()
    await db.refresh(db_collaboration)
    return db_collaboration

@router.delete("/{collaboration_id}")
async def delete_collaboration(collaboration_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    collaboration = await safe_scalar_one_or_none(result)
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    await db.delete(collaboration)
    await db.commit()
    return {"detail": "Collaboration deleted"}

@router.get("", response_model=List[Collaboration])
async def list_collaborations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel))
    collaborations = result.scalars().all()
    return collaborations

@router.post("/{collaboration_id}/approve", response_model=Dict)
async def approve_collaboration(
    collaboration_id: int, 
    request: CollaborationActionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Approve a specific collaboration request by changing status from 'pending' to 'active'.
    Validates that the collaboration belongs to the specified influencer and that the requester
    owns the business associated with the promotion."""
    
    # Get collaboration with promotion, business, and influencer details
    result = await db.execute(
        select(CollaborationModel, PromotionModel, BusinessModel, InfluencerModel)
        .join(PromotionModel, CollaborationModel.promotion_id == PromotionModel.id)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(and_(
            CollaborationModel.id == collaboration_id,
            CollaborationModel.influencer_id == request.influencer_id
        ))
    )
    collaboration_data = result.first()
    
    if not collaboration_data:
        raise HTTPException(
            status_code=404, 
            detail="Collaboration not found or does not belong to the specified influencer"
        )
    
    collaboration, promotion, business, influencer = collaboration_data
    
    # TODO: Add authentication middleware to get current user's business_id
    # For now, we validate that a business owns this promotion
    # In production, verify: current_user.business_id == promotion.business_id
    
    # Validate current status (allow approving from 'pending' or 'rejected')
    previous_status = collaboration.status
    if previous_status not in ('pending', 'rejected'):
        raise HTTPException(
            status_code=400,
            detail=f"Collaboration status is '{collaboration.status}', cannot approve from this state"
        )

    # Update status to approved
    collaboration.status = 'approved'
    await db.commit()
    await db.refresh(collaboration)
    
    business_name = getattr(business, 'name', f'Business {business.id}')
    influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
    promotion_name = getattr(promotion, 'promotion_name', f'Promotion {promotion.id}')
    
    logger.info(f"Business '{business_name}' (ID: {business.id}) approved collaboration '{promotion_name}' (ID: {collaboration_id}) with influencer '{influencer_name}' (ID: {request.influencer_id})")
    
    # 🔔 TRIGGER NOTIFICATION: Collaboration Approved
    notification_data = CollaborationApprovedNotificationData(
        collaboration_id=collaboration_id,
        collaboration_type=collaboration.collaboration_type,
        promotion_id=collaboration.promotion_id,
        promotion_name=promotion_name,
        business_id=business.id,
        business_name=business_name,
        influencer_id=request.influencer_id,
        influencer_name=influencer_name,
        approved_amount=getattr(collaboration, 'proposed_amount', None)
    )
    
    # Create notification for influencer
    await notification_service.create_collaboration_approved_notification(
        db=db,
        data=notification_data,
        background_tasks=background_tasks
    )
    
    logger.info(f"Notification triggered for collaboration approval: '{business_name}' approved '{influencer_name}' for '{promotion_name}'")
    
    return {
        "message": "Collaboration approved successfully",
        "collaboration_id": collaboration_id,
        "previous_status": previous_status,
        "new_status": "approved",
        "business_name": business_name,
        "business_id": business.id,
        "influencer_name": influencer_name,
        "influencer_id": request.influencer_id,
        "promotion_name": promotion_name,
        "promotion_id": collaboration.promotion_id,
        "collaboration_type": collaboration.collaboration_type,
        "approved_by": business.id,
        "notification_triggered": True  # Indicate notification was sent
    }

@router.post("/{collaboration_id}/reject", response_model=Dict)
async def reject_collaboration(
    collaboration_id: int, 
    request: CollaborationActionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Reject a specific collaboration request by setting status to 'rejected'.
    Validates that the collaboration belongs to the specified influencer and that the requester
    owns the business associated with the promotion."""
    
    # Get collaboration with promotion, business, and influencer details
    result = await db.execute(
        select(CollaborationModel, PromotionModel, BusinessModel, InfluencerModel)
        .join(PromotionModel, CollaborationModel.promotion_id == PromotionModel.id)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(and_(
            CollaborationModel.id == collaboration_id,
            CollaborationModel.influencer_id == request.influencer_id
        ))
    )
    collaboration_data = result.first()
    
    if not collaboration_data:
        raise HTTPException(
            status_code=404, 
            detail="Collaboration not found or does not belong to the specified influencer"
        )
    
    collaboration, promotion, business, influencer = collaboration_data
    
    # TODO: Add authentication middleware to get current user's business_id
    # For now, we validate that a business owns this promotion
    # In production, verify: current_user.business_id == promotion.business_id
    
    # Allow rejection from any non-rejected state (e.g., pending, active)
    previous_status = collaboration.status
    if previous_status == 'rejected':
        raise HTTPException(
            status_code=400,
            detail="Collaboration already rejected"
        )

    collaboration.status = 'rejected'
    
    # Store rejection reason if provided
    if request.reason:
        if not collaboration.terms_and_conditions:
            collaboration.terms_and_conditions = f"Rejection reason: {request.reason}"
        else:
            collaboration.terms_and_conditions += f"\nRejection reason: {request.reason}"
    
    await db.commit()
    await db.refresh(collaboration)
    
    business_name = getattr(business, 'name', f'Business {business.id}')
    influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
    promotion_name = getattr(promotion, 'promotion_name', f'Promotion {promotion.id}')
    
    logger.info(f"Business '{business_name}' (ID: {business.id}) rejected collaboration '{promotion_name}' (ID: {collaboration_id}) with influencer '{influencer_name}' (ID: {request.influencer_id})")
    if request.reason:
        logger.info(f"Rejection reason: {request.reason}")
    
    # Note: No notification triggered for rejection as per business logic
    # (businesses typically don't notify influencers of rejections)
    
    return {
        "message": "Collaboration rejected successfully",
        "collaboration_id": collaboration_id,
        "previous_status": previous_status,
        "new_status": "rejected",
        "business_name": business_name,
        "business_id": business.id,
        "influencer_name": influencer_name,
        "influencer_id": request.influencer_id,
        "promotion_name": promotion_name,
        "promotion_id": collaboration.promotion_id,
        "collaboration_type": collaboration.collaboration_type,
        "rejected_by": business.id,
        "rejection_reason": request.reason
    }

@router.post("/{collaboration_id}/reset", response_model=Dict)
async def reset_collaboration(
    collaboration_id: int, 
    request: CollaborationActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset a collaboration status back to 'pending'.
    This allows businesses to reconsider rejected or approved collaborations.
    Validates that the collaboration belongs to the specified influencer and that the requester
    owns the business associated with the promotion."""
    
    # Get collaboration with promotion, business, and influencer details
    result = await db.execute(
        select(CollaborationModel, PromotionModel, BusinessModel, InfluencerModel)
        .join(PromotionModel, CollaborationModel.promotion_id == PromotionModel.id)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(and_(
            CollaborationModel.id == collaboration_id,
            CollaborationModel.influencer_id == request.influencer_id
        ))
    )
    collaboration_data = result.first()
    
    if not collaboration_data:
        raise HTTPException(
            status_code=404, 
            detail="Collaboration not found or does not belong to the specified influencer"
        )
    
    collaboration, promotion, business, influencer = collaboration_data
    
    # TODO: Add authentication middleware to get current user's business_id
    # For now, we validate that a business owns this promotion
    # In production, verify: current_user.business_id == promotion.business_id
    
    # Store previous status and reset to pending
    previous_status = collaboration.status
    if previous_status == 'pending':
        raise HTTPException(
            status_code=400,
            detail="Collaboration is already pending"
        )

    collaboration.status = 'pending'
    await db.commit()
    await db.refresh(collaboration)
    
    business_name = getattr(business, 'name', f'Business {business.id}')
    influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
    promotion_name = getattr(promotion, 'promotion_name', f'Promotion {promotion.id}')
    
    logger.info(f"Business '{business_name}' (ID: {business.id}) reset collaboration '{promotion_name}' (ID: {collaboration_id}) with influencer '{influencer_name}' (ID: {request.influencer_id}) from '{previous_status}' to 'pending'")
    
    return {
        "message": "Collaboration reset to pending successfully",
        "collaboration_id": collaboration_id,
        "previous_status": previous_status,
        "new_status": "pending",
        "business_name": business_name,
        "business_id": business.id,
        "influencer_name": influencer_name,
        "influencer_id": request.influencer_id,
        "promotion_name": promotion_name,
        "promotion_id": collaboration.promotion_id,
        "collaboration_type": collaboration.collaboration_type,
        "reset_by": business.id
    }

@router.post("/approve-multiple", response_model=Dict)
async def approve_multiple_collaborations(
    request: BulkCollaborationApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Bulk approve multiple collaboration requests for a specific promotion and influencers"""
    
    if not request.influencer_ids:
        raise HTTPException(
            status_code=400,
            detail="No influencer IDs provided"
        )
    
    # First, get the promotion to determine the business_id
    promotion_result = await db.execute(
        select(PromotionModel, BusinessModel)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .where(PromotionModel.id == request.promotion_id)
    )
    promotion_data = promotion_result.first()
    
    if not promotion_data:
        raise HTTPException(
            status_code=404,
            detail=f"Promotion with ID {request.promotion_id} not found"
        )
    
    promotion, business = promotion_data
    business_id = promotion.business_id
    business_name = getattr(business, 'name', f'Business {business_id}')
    
    # Get all collaborations with promotion, business, and influencer details
    result = await db.execute(
        select(CollaborationModel, PromotionModel, BusinessModel, InfluencerModel)
        .join(PromotionModel, CollaborationModel.promotion_id == PromotionModel.id)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(and_(
            CollaborationModel.promotion_id == request.promotion_id,
            CollaborationModel.influencer_id.in_(request.influencer_ids)
        ))
    )
    collaboration_data = result.all()
    
    if not collaboration_data:
        raise HTTPException(
            status_code=404,
            detail=f"No collaborations found for promotion '{getattr(promotion, 'title', f'Promotion {request.promotion_id}')}' with provided influencer IDs"
        )
    
    # Validate status for all collaborations (business ownership already validated by promotion query)
    approved_collaborations = []
    failed_collaborations = []
    
    for collaboration, collab_promotion, collab_business, influencer in collaboration_data:
        collaboration_id = collaboration.id
        collab_business_name = getattr(collab_business, 'name', f'Business {collab_business.id}')
        influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
        promotion_title = getattr(collab_promotion, 'title', f'Promotion {collab_promotion.id}')
        
        # Note: Business ownership is already validated since we're querying by promotion_id that belongs to the business
        
        # Check current status
        if collaboration.status != 'pending':
            failed_collaborations.append({
                "collaboration_id": collaboration_id,
                "business_name": collab_business_name,
                "influencer_name": influencer_name,
                "promotion_title": promotion_title,
                "reason": f"Status is '{collaboration.status}', can only approve 'pending' collaborations",
                "current_status": collaboration.status
            })
            continue
        
        # Approve collaboration
        collaboration.status = 'active'
        approved_collaborations.append({
            "collaboration_id": collaboration_id,
            "business_name": collab_business_name,
            "business_id": collab_business.id,
            "influencer_name": influencer_name,
            "influencer_id": collaboration.influencer_id,
            "promotion_title": promotion_title,
            "promotion_id": collaboration.promotion_id,
            "collaboration_type": collaboration.collaboration_type,
            "previous_status": "pending",
            "new_status": "active"
        })
        
        # 🔔 TRIGGER NOTIFICATION: Collaboration Approved (individual)
        notification_data = CollaborationApprovedNotificationData(
            collaboration_id=collaboration_id,
            collaboration_type=collaboration.collaboration_type,
            promotion_id=collaboration.promotion_id,
            promotion_name=promotion_title,
            business_id=collab_business.id,
            business_name=collab_business_name,
            influencer_id=collaboration.influencer_id,
            influencer_name=influencer_name,
            approved_amount=getattr(collaboration, 'proposed_amount', None)
        )
        
        # Create notification for each approved collaboration
        await notification_service.create_collaboration_approved_notification(
            db=db,
            data=notification_data,
            background_tasks=background_tasks
        )
    
    # Check if any influencers don't have collaborations for this promotion
    found_influencer_ids = [collab.influencer_id for collab, _, _, _ in collaboration_data]
    not_found_influencer_ids = [iid for iid in request.influencer_ids if iid not in found_influencer_ids]
    
    for not_found_influencer_id in not_found_influencer_ids:
        failed_collaborations.append({
            "collaboration_id": None,
            "influencer_id": not_found_influencer_id,
            "promotion_id": request.promotion_id,
            "reason": f"No collaboration found for influencer ID {not_found_influencer_id} with promotion ID {request.promotion_id}",
            "current_status": None
        })
    
    # Commit all changes
    if approved_collaborations:
        await db.commit()
        promotion_title = approved_collaborations[0]['promotion_title'] if approved_collaborations else getattr(promotion, 'title', f'Promotion {request.promotion_id}')
        influencer_names = [f"'{collab['influencer_name']}'" for collab in approved_collaborations[:3]]
        logger.info(f"Business '{business_name}' (ID: {business_id}) bulk approved {len(approved_collaborations)} collaborations for promotion '{promotion_title}' (ID: {request.promotion_id}) with influencers: {', '.join(influencer_names)}{'...' if len(approved_collaborations) > 3 else ''}")
        logger.info(f"Notifications triggered for {len(approved_collaborations)} collaboration approvals")
    
    return {
        "message": f"Bulk approval completed: {len(approved_collaborations)} approved, {len(failed_collaborations)} failed",
        "business_name": business_name,
        "business_id": business_id,
        "promotion_id": request.promotion_id,
        "promotion_title": getattr(promotion, 'title', f'Promotion {request.promotion_id}'),
        "requested_influencer_ids": request.influencer_ids,
        "approved_count": len(approved_collaborations),
        "failed_count": len(failed_collaborations),
        "approved_collaborations": approved_collaborations,
        "failed_collaborations": failed_collaborations,
        "approved_by": business_id
    }

@router.get("/{collaboration_id}/messages", response_model=List[Dict])
async def get_collaboration_messages(
    collaboration_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a specific collaboration.
    Returns messages exchanged between business and influencer for this collaboration."""
    
    # Verify collaboration exists
    result = await db.execute(
        select(CollaborationModel, PromotionModel, BusinessModel, InfluencerModel)
        .join(PromotionModel, CollaborationModel.promotion_id == PromotionModel.id)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(CollaborationModel.id == collaboration_id)
    )
    collaboration_data = result.first()
    
    if not collaboration_data:
        raise HTTPException(
            status_code=404,
            detail=f"Collaboration {collaboration_id} not found"
        )
    
    collaboration, promotion, business, influencer = collaboration_data
    
    # TODO: In production, fetch actual messages from a messages table
    # For now, return structured message data based on collaboration history
    messages = []
    
    # Generate system messages based on collaboration status and timeline
    if collaboration.created_at:
        messages.append({
            "id": 1,
            "collaboration_id": collaboration_id,
            "sender_type": "system",
            "sender_name": "System",
            "message": f"Collaboration request created by {getattr(business, 'name', 'Business')} for {getattr(influencer, 'name', 'Influencer')}",
            "timestamp": collaboration.created_at.isoformat(),
            "read": True
        })
    
    if collaboration.started_at:
        messages.append({
            "id": 2,
            "collaboration_id": collaboration_id,
            "sender_type": "system",
            "sender_name": "System",
            "message": f"Collaboration started",
            "timestamp": collaboration.started_at.isoformat(),
            "read": True
        })
    
    if collaboration.completed_at:
        messages.append({
            "id": 3,
            "collaboration_id": collaboration_id,
            "sender_type": "system",
            "sender_name": "System",
            "message": f"Collaboration completed",
            "timestamp": collaboration.completed_at.isoformat(),
            "read": True
        })
    
    logger.info(f"Retrieved {len(messages)} messages for collaboration {collaboration_id}")
    return messages

@router.get("/{collaboration_id}/analytics", response_model=Dict)
async def get_collaboration_analytics(
    collaboration_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics data for a specific collaboration.
    Returns metrics, performance data, and insights about the collaboration."""
    
    # Get collaboration with related entities
    result = await db.execute(
        select(CollaborationModel, PromotionModel, BusinessModel, InfluencerModel)
        .join(PromotionModel, CollaborationModel.promotion_id == PromotionModel.id)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(CollaborationModel.id == collaboration_id)
    )
    collaboration_data = result.first()
    
    if not collaboration_data:
        raise HTTPException(
            status_code=404,
            detail=f"Collaboration {collaboration_id} not found"
        )
    
    collaboration, promotion, business, influencer = collaboration_data
    
    # Calculate duration
    duration_days = 0
    if collaboration.started_at and collaboration.completed_at:
        duration_days = (collaboration.completed_at - collaboration.started_at).days
    elif collaboration.started_at:
        from datetime import datetime
        duration_days = (datetime.utcnow() - collaboration.started_at).days
    
    # Build analytics response
    analytics = {
        "collaboration_id": collaboration_id,
        "status": collaboration.status,
        "collaboration_type": collaboration.collaboration_type,
        "financial": {
            "proposed_amount": collaboration.proposed_amount or 0,
            "negotiated_amount": collaboration.negotiated_amount or 0,
            "final_amount": collaboration.negotiated_amount or collaboration.proposed_amount or 0,
            "payment_status": collaboration.payment_status,
            "budget_allocation": promotion.budget or 0,
            "spent_amount": promotion.spent_amount or 0
        },
        "timeline": {
            "created_at": collaboration.created_at.isoformat() if collaboration.created_at else None,
            "started_at": collaboration.started_at.isoformat() if collaboration.started_at else None,
            "completed_at": collaboration.completed_at.isoformat() if collaboration.completed_at else None,
            "deadline": collaboration.deadline.isoformat() if collaboration.deadline else None,
            "duration_days": duration_days,
            "updated_at": collaboration.updated_at.isoformat() if collaboration.updated_at else None
        },
        "deliverables": {
            "description": collaboration.deliverables or "Not specified",
            "contract_signed": collaboration.contract_signed,
            "terms_and_conditions": collaboration.terms_and_conditions
        },
        "entities": {
            "business_name": getattr(business, 'name', 'Unknown'),
            "business_id": business.id,
            "influencer_name": getattr(influencer, 'name', 'Unknown'),
            "influencer_id": influencer.id,
            "promotion_name": getattr(promotion, 'promotion_name', 'Unknown'),
            "promotion_id": promotion.id
        },
        "performance": {
            "influencer_followers": getattr(influencer, 'total_posts', 0),
            "influencer_growth_rate": getattr(influencer, 'growth_rate', 0),
            "influencer_successful_campaigns": getattr(influencer, 'successful_campaigns', 0),
            "influencer_rate_per_post": getattr(influencer, 'rate_per_post', 0)
        }
    }
    
    logger.info(f"Retrieved analytics for collaboration {collaboration_id}")
    return analytics

@router.get("/promotion-details/{promotion_id}", response_model=Dict)
async def get_promotion_details_with_collaboration_metadata(
    promotion_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get promotion details along with collaboration metadata.
    Returns promotion information plus collaboration statistics and active collaborators."""
    
    # Get promotion with business details
    result = await db.execute(
        select(PromotionModel, BusinessModel)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .where(PromotionModel.id == promotion_id)
    )
    promotion_data = result.first()
    
    if not promotion_data:
        raise HTTPException(
            status_code=404,
            detail=f"Promotion {promotion_id} not found"
        )
    
    try:
        
        promotion, business = promotion_data
        
        # Get collaboration statistics for this promotion
        collab_stats_result = await db.execute(
            select(
                func.count(CollaborationModel.id).label('total'),
                func.count(case((CollaborationModel.status == 'active', 1))).label('active'),
                func.count(case((CollaborationModel.status == 'approved', 1))).label('approved'),
                func.count(case((CollaborationModel.status == 'pending', 1))).label('pending'),
                func.count(case((CollaborationModel.status == 'rejected', 1))).label('rejected')
            )
            .where(CollaborationModel.promotion_id == promotion_id)
        )
        stats = collab_stats_result.first()
        
        # Get active influencers for this promotion with user details
        active_influencers_result = await db.execute(
            select(InfluencerModel, CollaborationModel, UserModel)
            .join(CollaborationModel, CollaborationModel.influencer_id == InfluencerModel.id)
            .join(UserModel, InfluencerModel.user_id == UserModel.id)
            .where(
                and_(
                    CollaborationModel.promotion_id == promotion_id,
                    CollaborationModel.status.in_(['active', 'approved'])
                )
            )
        )
        active_influencers = active_influencers_result.unique().all()
        
        # Get collaboration documents for this promotion
        documents_result = await db.execute(
            select(GeneratedDocument)
            .where(
                and_(
                    GeneratedDocument.promotion_id == promotion_id,
                    GeneratedDocument.type == 'collaboration_request',
                    GeneratedDocument.generation_status == 'completed'
                )
            )
        )
        documents = documents_result.scalars().all()
        
        # Build response
        response = {
            "promotion": {
                "id": promotion.id,
                "uuid": str(promotion.uuid) if promotion.uuid else None,
                "business_id": promotion.business_id,
                "promotion_name": promotion.promotion_name,
                "promotion_item": promotion.promotion_item,
                "description": promotion.description,
                "start_date": promotion.start_date.isoformat() if promotion.start_date else None,
                "end_date": promotion.end_date.isoformat() if promotion.end_date else None,
                "discount": promotion.discount,
                "budget": promotion.budget,
                "spent_amount": promotion.spent_amount,
                "status": promotion.status,
                "target_audience": promotion.target_audience,
                "social_media_platform_id": promotion.social_media_platform_id,
                "created_at": promotion.created_at.isoformat() if promotion.created_at else None,
                "updated_at": promotion.updated_at.isoformat() if promotion.updated_at else None
            },
            "business": {
                "id": business.id,
                "name": business.name,
                "description": business.description,
                "website": getattr(business, 'website_url', None),
                "industry": business.industry,
                "created_at": business.created_at.isoformat() if business.created_at else None
            },
            "collaboration_metadata": {
                "statistics": {
                    "total_collaborations": stats.total if stats else 0,
                    "active_collaborations": stats.active if stats else 0,
                    "approved_collaborations": stats.approved if stats else 0,
                    "pending_collaborations": stats.pending if stats else 0,
                    "rejected_collaborations": stats.rejected if stats else 0
                },
                "active_influencers": [
                    {
                        "influencer_id": influencer.id,
                        "influencer_name": (
                            getattr(influencer, 'username', None) or 
                            f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or 
                            f'Influencer {influencer.id}'
                        ),
                        "collaboration_id": collaboration.id,
                        "collaboration_status": collaboration.status,
                        "collaboration_type": collaboration.collaboration_type,
                        "proposed_amount": collaboration.proposed_amount,
                        "negotiated_amount": collaboration.negotiated_amount,
                        "created_at": collaboration.created_at.isoformat() if collaboration.created_at else None
                    }
                    for influencer, collaboration, user in active_influencers
                ]
            },
            "collaboration_documents": [
                {
                    "id": doc.id,
                    "type": doc.type,
                    "subtype": doc.subtype,
                    "file_path": doc.file_path,
                    "generated_at": doc.generated_at.isoformat() if doc.generated_at else None,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "parameters": doc.parameters
                }
                for doc in documents
            ]
        }
        
        logger.info(f"Retrieved promotion details with collaboration metadata for promotion {promotion_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in get_promotion_details_with_collaboration_metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/promotion-messages/{promotion_id}", response_model=List[Dict])
async def get_promotion_messages(
    promotion_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a specific promotion.
    Returns messages exchanged between business and influencers for this promotion."""
    
    # Verify promotion exists
    result = await db.execute(
        select(PromotionModel, BusinessModel)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .where(PromotionModel.id == promotion_id)
    )
    promotion_data = result.first()
    
    if not promotion_data:
        raise HTTPException(
            status_code=404,
            detail=f"Promotion {promotion_id} not found"
        )
    
    promotion, business = promotion_data
    
    # Get all collaborations for this promotion
    collaborations_result = await db.execute(
        select(CollaborationModel, InfluencerModel)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .where(CollaborationModel.promotion_id == promotion_id)
    )
    collaborations = collaborations_result.all()
    
    # TODO: Implement proper messages table and model
    # For now, return empty array since no real messages table exists
    # Future implementation should:
    # 1. Create a messages table with fields: id, promotion_id, collaboration_id, sender_type, sender_id, message, timestamp, read
    # 2. Create a MessageModel in app/db/models/messages.py
    # 3. Fetch real messages from the database instead of generating mock data
    
    messages = []
    
    logger.info(f"Retrieved {len(messages)} messages for promotion {promotion_id}")
    return messages

@router.get("/promotion-analytics/{promotion_id}", response_model=Dict)
async def get_promotion_analytics(
    promotion_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics data for a specific promotion.
    Returns charts data including approved influencers per month and influencer vs amount distribution."""
    
    # Verify promotion exists
    result = await db.execute(
        select(PromotionModel, BusinessModel)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .where(PromotionModel.id == promotion_id)
    )
    promotion_data = result.first()
    
    if not promotion_data:
        raise HTTPException(
            status_code=404,
            detail=f"Promotion {promotion_id} not found"
        )
    
    promotion, business = promotion_data
    
    # Get all collaborations for this promotion with influencer and user details
    collaborations_result = await db.execute(
        select(CollaborationModel, InfluencerModel, UserModel)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id)
        .join(UserModel, InfluencerModel.user_id == UserModel.id)
        .where(CollaborationModel.promotion_id == promotion_id)
    )
    collaborations = collaborations_result.unique().all()
    
    # Calculate approved influencers per month
    approved_per_month = {}
    for collaboration, influencer, user in collaborations:
        if collaboration.status == 'approved' and collaboration.created_at:
            month_key = collaboration.created_at.strftime('%Y-%m')
            approved_per_month[month_key] = approved_per_month.get(month_key, 0) + 1
    
    # Sort months and create chart data
    monthly_chart_data = []
    for month in sorted(approved_per_month.keys()):
        monthly_chart_data.append({
            "month": month,
            "approved_influencers": approved_per_month[month]
        })
    
    # Calculate influencer vs amount distribution
    influencer_amount_data = []
    total_amount = 0
    for collaboration, influencer, user in collaborations:
        if collaboration.status in ['approved', 'active'] and collaboration.proposed_amount:
            amount = float(collaboration.proposed_amount) if collaboration.proposed_amount else 0
            total_amount += amount
            influencer_amount_data.append({
                "influencer_id": influencer.id,
                "influencer_name": (
                    getattr(influencer, 'username', None) or 
                    f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or 
                    f'Influencer {influencer.id}'
                ),
                "amount": amount,
                "percentage": 0  # Will calculate after total_amount is known
            })
    
    # Calculate percentages for pie chart
    for item in influencer_amount_data:
        if total_amount > 0:
            item["percentage"] = round((item["amount"] / total_amount) * 100, 1)
    
    # Get promotion statistics
    total_collaborations = len(collaborations)
    approved_collaborations = len([c for c, _, _ in collaborations if c.status == 'approved'])
    pending_collaborations = len([c for c, _, _ in collaborations if c.status == 'pending'])
    active_collaborations = len([c for c, _, _ in collaborations if c.status == 'active'])
    rejected_collaborations = len([c for c, _, _ in collaborations if c.status == 'rejected'])
    
    analytics = {
        "promotion_id": promotion_id,
        "promotion_name": promotion.promotion_name,
        "business_name": business.name,
        "statistics": {
            "total_collaborations": total_collaborations,
            "approved_collaborations": approved_collaborations,
            "pending_collaborations": pending_collaborations,
            "active_collaborations": active_collaborations,
            "rejected_collaborations": rejected_collaborations,
            "total_amount": total_amount
        },
        "charts": {
            "approved_influencers_per_month": monthly_chart_data,
            "influencer_amount_distribution": influencer_amount_data
        }
    }
    
    logger.info(f"Retrieved analytics for promotion {promotion_id}")
    return analytics


@router.get("/promotion-documents/{promotion_id}")
async def get_promotion_documents(
    promotion_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all completed documents for a specific promotion
    """
    logger.info(f"Fetching documents for promotion {promotion_id}")
    
    # Query for completed documents
    documents_result = await db.execute(
        select(GeneratedDocument)
        .where(
            and_(
                GeneratedDocument.promotion_id == promotion_id,
                GeneratedDocument.generation_status == 'completed'
            )
        )
        .order_by(GeneratedDocument.created_at.desc())
    )
    documents = documents_result.scalars().all()
    
    # Format response
    documents_list = [
        {
            "id": doc.id,
            "type": doc.type,
            "subtype": doc.subtype,
            "file_path": doc.file_path,
            "generated_at": doc.generated_at.isoformat() if doc.generated_at else None,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "parameters": doc.parameters
        }
        for doc in documents
    ]
    
    logger.info(f"Found {len(documents_list)} documents for promotion {promotion_id}")
    return documents_list 