from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, or_
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import logging
import json

from app.db.session import get_db
from app.db.models.notification import Notification, NotificationPreference
from app.db.models.user import User
from app.core.query_helpers import safe_scalar_one_or_none
from app.schemas.notification import (
    NotificationResponse,
    NotificationListRequest,
    NotificationListResponse, 
    NotificationPreferenceResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationStatsResponse,
    BulkMarkReadRequest,
    BulkDeleteRequest,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    WebSocketMessage
)
from app.core.dependencies import get_current_user
from app.services.notification_service import notification_service
from app.services.websocket_service import websocket_service

router = APIRouter(prefix="/notifications", tags=["notifications"])
security = HTTPBearer()

logger = logging.getLogger(__name__)

# ============================================================================
# NOTIFICATION CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    read_status: Optional[bool] = Query(None, description="Filter by read status (true=read, false=unread, null=all)"),
    date_from: Optional[datetime] = Query(None, description="Filter notifications from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter notifications to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated notifications for the current user with optional filters"""
    
    result = await notification_service.get_notifications(
        db=db,
        user_id=current_user.id,
        event_type=event_type,
        read_status=read_status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit
    )
    
    return NotificationListResponse(
        notifications=[NotificationResponse.from_orm(n) for n in result["notifications"]],
        total_count=result["total_count"],
        unread_count=result["unread_count"],
        page=result["page"],
        limit=result["limit"],
        has_next=result["has_next"],
        has_prev=result["has_prev"]
    )

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification by ID"""
    
    result = await db.execute(
        select(Notification)
        .where(and_(
            Notification.id == notification_id,
            Notification.recipient_user_id == current_user.id
        ))
    )
    notification = await safe_scalar_one_or_none(result)
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    return NotificationResponse.from_orm(notification)

@router.put("/{notification_id}/mark-read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read"""
    
    notification = await notification_service.mark_notification_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    # Send WebSocket update
    await websocket_service.send_notification_update(
        user_id=current_user.id,
        notification_id=notification_id,
        update_data={"read_at": notification.read_at.isoformat() if notification.read_at else None}
    )
    
    return NotificationResponse.from_orm(notification)

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification"""
    
    success = await notification_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    return {"message": "Notification deleted successfully"}

@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification statistics for the current user"""
    
    # Get various counts
    stats_query = await db.execute(
        select(
            func.count(Notification.id).label('total_notifications'),
            func.count().filter(Notification.read_at.is_(None)).label('unread_count'),
            func.count().filter(Notification.email_sent == True).label('email_sent_count'),
            func.count().filter(Notification.twitter_posted == True).label('twitter_posted_count'),
            func.count().filter(Notification.email_error.isnot(None)).label('failed_emails'),
            func.count().filter(Notification.twitter_error.isnot(None)).label('failed_twitter_posts')
        )
        .where(Notification.recipient_user_id == current_user.id)
    )
    stats = stats_query.first()
    
    return NotificationStatsResponse(
        total_notifications=stats.total_notifications or 0,
        unread_count=stats.unread_count or 0,
        email_sent_count=stats.email_sent_count or 0,
        twitter_posted_count=stats.twitter_posted_count or 0,
        failed_emails=stats.failed_emails or 0,
        failed_twitter_posts=stats.failed_twitter_posts or 0
    )

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get unread notification count for the current user"""
    
    result = await db.execute(
        select(func.count(Notification.id))
        .where(and_(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None)
        ))
    )
    unread_count = result.scalar()
    
    return {"unread_count": unread_count}

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read for the current user"""
    
    # Update all unread notifications
    result = await db.execute(
        select(Notification)
        .where(and_(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None)
        ))
    )
    notifications = result.scalars().all()
    
    current_time = datetime.utcnow()
    for notification in notifications:
        notification.read_at = current_time
    
    await db.commit()
    
    # Send WebSocket update
    await websocket_service.send_unread_count_update(
        user_id=current_user.id,
        unread_count=0
    )
    
    logger.info(f"Marked {len(notifications)} notifications as read for user {current_user.id}")
    
    return {
        "message": f"Marked {len(notifications)} notifications as read",
        "updated_count": len(notifications)
    }

@router.put("/bulk-mark-read")
async def bulk_mark_notifications_read(
    request: BulkMarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark multiple specific notifications as read"""
    
    # Get notifications to update
    result = await db.execute(
        select(Notification)
        .where(and_(
            Notification.id.in_(request.notification_ids),
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None)
        ))
    )
    notifications = result.scalars().all()
    
    if not notifications:
        raise HTTPException(
            status_code=404,
            detail="No unread notifications found with the provided IDs"
        )
    
    # Update notifications
    current_time = datetime.utcnow()
    for notification in notifications:
        notification.read_at = current_time
    
    await db.commit()
    
    # Send WebSocket updates
    for notification in notifications:
        await websocket_service.send_notification_update(
            user_id=current_user.id,
            notification_id=notification.id,
            update_data={"read_at": current_time.isoformat()}
        )
    
    return {
        "message": f"Marked {len(notifications)} notifications as read",
        "updated_count": len(notifications),
        "updated_ids": [str(n.id) for n in notifications]
    }

@router.delete("/bulk-delete")
async def bulk_delete_notifications(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple notifications"""
    
    # Get notifications to delete
    result = await db.execute(
        select(Notification)
        .where(and_(
            Notification.id.in_(request.notification_ids),
            Notification.recipient_user_id == current_user.id
        ))
    )
    notifications = result.scalars().all()
    
    if not notifications:
        raise HTTPException(
            status_code=404,
            detail="No notifications found with the provided IDs"
        )
    
    # Delete notifications
    for notification in notifications:
        await db.delete(notification)
    
    await db.commit()
    
    return {
        "message": f"Deleted {len(notifications)} notifications",
        "deleted_count": len(notifications),
        "deleted_ids": [str(n.id) for n in notifications]
    }

# ============================================================================
# USER PREFERENCES
# ============================================================================

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification preferences for the current user"""
    
    result = await db.execute(
        select(NotificationPreference)
        .where(NotificationPreference.user_id == current_user.id)
    )
    preferences = result.scalars().all()
    
    return UserPreferencesResponse(
        user_id=current_user.id,
        preferences=[NotificationPreferenceResponse.from_orm(p) for p in preferences]
    )

@router.post("/preferences/{event_type}", response_model=NotificationPreferenceResponse)
async def create_notification_preference(
    event_type: str,
    email_enabled: bool = True,
    in_app_enabled: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update notification preference for specific event type"""
    
    # Check if preference already exists
    result = await db.execute(
        select(NotificationPreference)
        .where(and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.event_type == event_type
        ))
    )
    existing_preference = await safe_scalar_one_or_none(result)
    
    if existing_preference:
        # Update existing preference
        existing_preference.email_enabled = email_enabled
        existing_preference.in_app_enabled = in_app_enabled
        await db.commit()
        await db.refresh(existing_preference)
        return NotificationPreferenceResponse.from_orm(existing_preference)
    else:
        # Create new preference
        preference_data = NotificationPreferenceCreate(
            user_id=current_user.id,
            event_type=event_type,
            email_enabled=email_enabled,
            in_app_enabled=in_app_enabled
        )
        
        db_preference = NotificationPreference(**preference_data.dict())
        db.add(db_preference)
        await db.commit()
        await db.refresh(db_preference)
        
        logger.info(f"Created notification preference for user {current_user.id}, event type {event_type}")
        return NotificationPreferenceResponse.from_orm(db_preference)

@router.put("/preferences/{event_type}", response_model=NotificationPreferenceResponse)
async def update_notification_preference(
    event_type: str,
    update_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update notification preference for specific event type"""
    
    result = await db.execute(
        select(NotificationPreference)
        .where(and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.event_type == event_type
        ))
    )
    preference = await safe_scalar_one_or_none(result)
    
    if not preference:
        raise HTTPException(
            status_code=404,
            detail="Notification preference not found"
        )
    
    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(preference, field, value)
    
    await db.commit()
    await db.refresh(preference)
    
    logger.info(f"Updated notification preference for user {current_user.id}, event type {event_type}")
    return NotificationPreferenceResponse.from_orm(preference)

@router.delete("/preferences/{event_type}")
async def delete_notification_preference(
    event_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete notification preference for specific event type (revert to defaults)"""
    
    result = await db.execute(
        select(NotificationPreference)
        .where(and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.event_type == event_type
        ))
    )
    preference = await safe_scalar_one_or_none(result)
    
    if not preference:
        raise HTTPException(
            status_code=404,
            detail="Notification preference not found"
        )
    
    await db.delete(preference)
    await db.commit()
    
    logger.info(f"Deleted notification preference for user {current_user.id}, event type {event_type}")
    return {"message": "Notification preference deleted (reverted to defaults)"}

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    # Note: WebSocket doesn't support standard HTTP authentication
    # In production, you'd want to implement WebSocket authentication
):
    """WebSocket endpoint for real-time notifications"""
    
    try:
        # Connect user
        await websocket_service.connect_user(websocket, user_id)
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle the message
                await websocket_service.handle_client_message(websocket, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'data': {'message': 'Invalid JSON format'}
                }))
            except Exception as e:
                logger.error(f"Error in WebSocket message handling: {str(e)}")
                await websocket.send_text(json.dumps({
                    'type': 'error', 
                    'data': {'message': 'Internal server error'}
                }))
                
    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {str(e)}")
    finally:
        # Disconnect user
        websocket_service.disconnect_user(websocket)

# ============================================================================
# ADMIN ENDPOINTS (Optional - for system monitoring)
# ============================================================================

@router.get("/admin/stats")
async def get_system_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide notification statistics (admin only)"""
    
    # TODO: Add admin role check
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    # System-wide stats
    system_stats = await db.execute(
        select(
            func.count(Notification.id).label('total_notifications'),
            func.count().filter(Notification.read_at.is_(None)).label('total_unread'),
            func.count().filter(Notification.email_sent == True).label('total_emails_sent'),
            func.count().filter(Notification.twitter_posted == True).label('total_tweets_posted'),
            func.count().filter(Notification.email_error.isnot(None)).label('total_email_failures'),
            func.count().filter(Notification.twitter_error.isnot(None)).label('total_twitter_failures')
        )
    )
    stats = system_stats.first()
    
    # WebSocket connection stats
    ws_stats = websocket_service.get_connection_stats()
    
    return {
        "system_stats": {
            "total_notifications": stats.total_notifications or 0,
            "total_unread": stats.total_unread or 0,
            "total_emails_sent": stats.total_emails_sent or 0,
            "total_tweets_posted": stats.total_tweets_posted or 0,
            "total_email_failures": stats.total_email_failures or 0,
            "total_twitter_failures": stats.total_twitter_failures or 0
        },
        "websocket_stats": ws_stats
    } 