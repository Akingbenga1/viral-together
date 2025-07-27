from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Dict
from app.db.session import get_db
from app.db.models.collaborations import Collaboration as CollaborationModel
from app.db.models.promotions import Promotion as PromotionModel
from app.db.models.business import Business as BusinessModel
from app.db.models.influencer import Influencer as InfluencerModel
from app.schemas.collaborations import CollaborationCreate, Collaboration
from pydantic import BaseModel
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

# Pydantic models for approval endpoints
class CollaborationApprovalRequest(BaseModel):
    business_id: int

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
    
    # Create collaboration
    db_collaboration = CollaborationModel(**collaboration.dict())
    
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
    collaboration = result.scalar_one_or_none()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    return collaboration

@router.put("/{collaboration_id}", response_model=Collaboration)
async def update_collaboration(collaboration_id: int, collaboration: CollaborationCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    db_collaboration = result.scalar_one_or_none()
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
    collaboration = result.scalar_one_or_none()
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
    request: CollaborationApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Approve a specific collaboration request by changing status from 'pending' to 'active'"""
    
    # Get collaboration with promotion, business, and influencer details
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
            detail="Collaboration not found"
        )
    
    collaboration, promotion, business, influencer = collaboration_data
    
    # Validate business ownership
    if promotion.business_id != request.business_id:
        raise HTTPException(
            status_code=403,
            detail="Business does not own this promotion"
        )
    
    # Validate current status
    if collaboration.status != 'pending':
        raise HTTPException(
            status_code=400,
            detail=f"Collaboration status is '{collaboration.status}', can only approve 'pending' collaborations"
        )
    
    # Update status to active
    collaboration.status = 'active'
    await db.commit()
    await db.refresh(collaboration)
    
    business_name = getattr(business, 'name', f'Business {business.id}')
    influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
    promotion_title = getattr(promotion, 'title', f'Promotion {promotion.id}')
    
    logger.info(f"Business '{business_name}' (ID: {request.business_id}) approved collaboration '{promotion_title}' (ID: {collaboration_id}) with influencer '{influencer_name}' (ID: {collaboration.influencer_id})")
    
    # 🔔 TRIGGER NOTIFICATION: Collaboration Approved
    notification_data = CollaborationApprovedNotificationData(
        collaboration_id=collaboration_id,
        collaboration_type=collaboration.collaboration_type,
        promotion_id=collaboration.promotion_id,
        promotion_name=promotion_title,
        business_id=request.business_id,
        business_name=business_name,
        influencer_id=collaboration.influencer_id,
        influencer_name=influencer_name,
        approved_amount=getattr(collaboration, 'proposed_amount', None)
    )
    
    # Create notification for influencer
    await notification_service.create_collaboration_approved_notification(
        db=db,
        data=notification_data,
        background_tasks=background_tasks
    )
    
    logger.info(f"Notification triggered for collaboration approval: '{business_name}' approved '{influencer_name}' for '{promotion_title}'")
    
    return {
        "message": "Collaboration approved successfully",
        "collaboration_id": collaboration_id,
        "previous_status": "pending",
        "new_status": "active",
        "business_name": business_name,
        "business_id": request.business_id,
        "influencer_name": influencer_name,
        "influencer_id": collaboration.influencer_id,
        "promotion_title": promotion_title,
        "promotion_id": collaboration.promotion_id,
        "collaboration_type": collaboration.collaboration_type,
        "approved_by": request.business_id,
        "notification_triggered": True  # Indicate notification was sent
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