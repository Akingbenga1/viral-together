from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from datetime import datetime, timedelta
from calendar import month_name

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserRead
from app.db.models.user import User
from app.db.models.business import Business
from app.db.models.role import Role
from app.db.models.user_subscription import UserSubscription
from app.db.models.subscription import SubscriptionPlan

router = APIRouter()

@router.get("/user-registrations-by-month")
async def get_user_registrations_by_month(
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user registrations grouped by month for the current year
    """
    try:
        # Check if user has admin privileges
        user_roles = [role.name for role in current_user.roles] if current_user.roles else []
        if "admin" not in user_roles and "super_admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get current year
        current_year = datetime.now().year
        
        # Query to get user registrations grouped by month
        query = select(
            extract('month', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).where(
            extract('year', User.created_at) == current_year
        ).group_by(
            extract('month', User.created_at)
        ).order_by(
            extract('month', User.created_at)
        )
        
        result = await db.execute(query)
        monthly_data = result.fetchall()
        
        # Create a dictionary with all months initialized to 0
        month_data = {i: 0 for i in range(1, 13)}
        
        # Fill in actual data
        for row in monthly_data:
            month_data[int(row.month)] = int(row.count)
        
        # Format response
        response_data = []
        for month_num in range(1, 13):
            response_data.append({
                "month": month_name[month_num][:3],  # Jan, Feb, Mar, etc.
                "month_number": month_num,
                "registrations": month_data[month_num]
            })
        
        return {
            "success": True,
            "year": current_year,
            "data": response_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user registration data: {str(e)}")

@router.get("/business-registrations-by-month")
async def get_business_registrations_by_month(
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get business registrations grouped by month for the current year
    """
    try:
        # Check if user has admin privileges
        user_roles = [role.name for role in current_user.roles] if current_user.roles else []
        if "admin" not in user_roles and "super_admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get current year
        current_year = datetime.now().year
        
        # Query to get business registrations grouped by month
        query = select(
            extract('month', Business.created_at).label('month'),
            func.count(Business.id).label('count')
        ).where(
            extract('year', Business.created_at) == current_year
        ).group_by(
            extract('month', Business.created_at)
        ).order_by(
            extract('month', Business.created_at)
        )
        
        result = await db.execute(query)
        monthly_data = result.fetchall()
        
        # Create a dictionary with all months initialized to 0
        month_data = {i: 0 for i in range(1, 13)}
        
        # Fill in actual data
        for row in monthly_data:
            month_data[int(row.month)] = int(row.count)
        
        # Format response
        response_data = []
        for month_num in range(1, 13):
            response_data.append({
                "month": month_name[month_num][:3],  # Jan, Feb, Mar, etc.
                "month_number": month_num,
                "registrations": month_data[month_num]
            })
        
        return {
            "success": True,
            "year": current_year,
            "data": response_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching business registration data: {str(e)}")

@router.get("/analytics-summary")
async def get_analytics_summary(
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall analytics summary for admin dashboard
    """
    try:
        # Check if user has admin privileges
        user_roles = [role.name for role in current_user.roles] if current_user.roles else []
        if "admin" not in user_roles and "super_admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get current date and date 30 days ago
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Total users count
        total_users_query = select(func.count(User.id))
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar()
        
        # New users in last 30 days
        new_users_query = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
        new_users_result = await db.execute(new_users_query)
        new_users_30d = new_users_result.scalar()
        
        # Total businesses count
        total_businesses_query = select(func.count(Business.id))
        total_businesses_result = await db.execute(total_businesses_query)
        total_businesses = total_businesses_result.scalar()
        
        # New businesses in last 30 days
        new_businesses_query = select(func.count(Business.id)).where(Business.created_at >= thirty_days_ago)
        new_businesses_result = await db.execute(new_businesses_query)
        new_businesses_30d = new_businesses_result.scalar()
        
        return {
            "success": True,
            "data": {
                "total_users": total_users,
                "new_users_30d": new_users_30d,
                "total_businesses": total_businesses,
                "new_businesses_30d": new_businesses_30d,
                "period": "last_30_days"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics summary: {str(e)}")

@router.get("/monthly-subscription-revenue")
async def get_monthly_subscription_revenue(
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get monthly subscription revenue grouped by month for the current year
    """
    try:
        # Check if user has admin privileges
        user_roles = [role.name for role in current_user.roles] if current_user.roles else []
        if "admin" not in user_roles and "super_admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get current year
        current_year = datetime.now().year
        
        # Query to get monthly subscription revenue
        # We'll use the created_at date of the subscription to determine the month
        query = select(
            extract('month', UserSubscription.created_at).label('month'),
            func.sum(SubscriptionPlan.price_per_month).label('total_revenue')
        ).join(
            SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id
        ).where(
            extract('year', UserSubscription.created_at) == current_year,
            UserSubscription.status.in_(['active', 'trialing'])  # Only count active subscriptions
        ).group_by(
            extract('month', UserSubscription.created_at)
        ).order_by(
            extract('month', UserSubscription.created_at)
        )
        
        result = await db.execute(query)
        monthly_data = result.fetchall()
        
        # Create a dictionary with all months initialized to 0
        month_data = {i: 0.0 for i in range(1, 13)}
        
        # Fill in actual data
        for row in monthly_data:
            month_data[int(row.month)] = float(row.total_revenue) if row.total_revenue else 0.0
        
        # Format response
        response_data = []
        for month_num in range(1, 13):
            response_data.append({
                "month": month_name[month_num][:3],  # Jan, Feb, Mar, etc.
                "month_number": month_num,
                "revenue": month_data[month_num]
            })
        
        return {
            "success": True,
            "year": current_year,
            "data": response_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly subscription revenue: {str(e)}")
