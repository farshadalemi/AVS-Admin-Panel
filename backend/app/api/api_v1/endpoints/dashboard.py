from typing import Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import crud, models
from app.api import deps

router = APIRouter()


@router.get("/admin")
def read_admin_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get comprehensive admin dashboard data
    """
    now = datetime.utcnow()
    
    # Get subscription analytics
    subscription_analytics = crud.subscription.get_subscription_analytics(db)
    
    # Get usage analytics for last 30 days
    thirty_days_ago = now - timedelta(days=30)
    usage_analytics = crud.usage.get_system_usage_analytics(
        db, start_date=thirty_days_ago, end_date=now
    )
    
    # Get revenue stats for current month
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = crud.subscription.get_revenue_stats(
        db, start_date=current_month_start, end_date=now
    )
    
    # Get user statistics
    total_users = crud.user.count(db)
    active_users_count = (
        db.query(func.count(models.User.id))
        .filter(models.User.is_active == True)
        .scalar()
    )
    
    # Get recent activity (last 10 subscriptions and usage records)
    recent_subscriptions = crud.subscription.get_subscriptions_with_details(
        db, skip=0, limit=10
    )
    recent_usage = crud.usage.get_usage_with_user_details(
        db, skip=0, limit=10
    )
    
    # Get expiring subscriptions (next 7 days)
    expiring_subscriptions = crud.subscription.get_expiring_subscriptions(
        db, days_ahead=7, limit=20
    )
    
    # Get popular plans
    popular_plans = crud.plan.get_popular_plans(db, limit=5)
    
    # Get active calls
    active_calls = crud.usage.get_active_calls(db)
    
    return {
        "overview": {
            "total_users": total_users,
            "active_users": active_users_count,
            "total_subscriptions": subscription_analytics["total_subscriptions"],
            "active_subscriptions": subscription_analytics["active_subscriptions"],
            "monthly_revenue": monthly_revenue["total_revenue"],
            "total_revenue": subscription_analytics["total_revenue"],
            "active_calls": len(active_calls),
        },
        "subscription_analytics": subscription_analytics,
        "usage_analytics": usage_analytics,
        "monthly_revenue": monthly_revenue,
        "recent_activity": {
            "subscriptions": recent_subscriptions[:5],  # Last 5 subscriptions
            "usage": recent_usage[:5],  # Last 5 usage records
        },
        "alerts": {
            "expiring_subscriptions": len(expiring_subscriptions),
            "expiring_subscriptions_list": expiring_subscriptions,
        },
        "popular_plans": popular_plans,
        "active_calls": active_calls,
    }


@router.get("/user")
def read_user_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get user dashboard data
    """
    # Get user's dashboard stats (already implemented in user CRUD)
    dashboard_data = crud.user.get_user_dashboard_stats(db, user_id=current_user.id)
    
    # Get recent usage (last 10 records)
    recent_usage = crud.usage.get_user_usage(
        db, user_id=current_user.id, skip=0, limit=10
    )
    
    # Get current month usage stats
    now = datetime.utcnow()
    current_month_usage = crud.usage.get_user_monthly_usage(
        db, user_id=current_user.id, year=now.year, month=now.month
    )
    
    # Calculate usage limits and warnings
    warnings = []
    if dashboard_data.get("active_subscription"):
        subscription = dashboard_data["active_subscription"]
        current_usage = dashboard_data["current_month_usage"]
        
        # Check call limit
        if subscription.get("max_calls"):
            calls_used = current_usage["total_calls"]
            calls_limit = subscription["max_calls"]
            calls_percentage = (calls_used / calls_limit) * 100
            
            if calls_percentage >= 90:
                warnings.append({
                    "type": "calls_limit",
                    "message": f"You've used {calls_percentage:.1f}% of your monthly call limit",
                    "severity": "high" if calls_percentage >= 95 else "medium"
                })
        
        # Check minutes limit
        if subscription.get("max_minutes"):
            minutes_used = current_usage["total_duration"] / 60
            minutes_limit = subscription["max_minutes"]
            minutes_percentage = (minutes_used / minutes_limit) * 100
            
            if minutes_percentage >= 90:
                warnings.append({
                    "type": "minutes_limit",
                    "message": f"You've used {minutes_percentage:.1f}% of your monthly minutes limit",
                    "severity": "high" if minutes_percentage >= 95 else "medium"
                })
        
        # Check subscription expiry
        if subscription.get("end_date"):
            end_date = subscription["end_date"]
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            days_remaining = (end_date - now).days
            if days_remaining <= 7:
                warnings.append({
                    "type": "subscription_expiry",
                    "message": f"Your subscription expires in {days_remaining} days",
                    "severity": "high" if days_remaining <= 3 else "medium"
                })
    
    return {
        **dashboard_data,
        "recent_usage": recent_usage,
        "current_month_detailed": current_month_usage,
        "warnings": warnings,
    }


@router.get("/stats/overview")
def read_overview_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get quick overview statistics for admin dashboard
    """
    now = datetime.utcnow()
    
    # Total counts
    total_users = crud.user.count(db)
    total_plans = crud.plan.count(db)
    total_subscriptions = crud.subscription.count(db)
    total_usage_records = crud.usage.count(db)
    
    # Active counts
    active_users = (
        db.query(func.count(models.User.id))
        .filter(models.User.is_active == True)
        .scalar()
    )
    
    active_subscriptions = (
        db.query(func.count(models.Subscription.id))
        .filter(
            models.Subscription.is_active == True,
            models.Subscription.end_date > now
        )
        .scalar()
    )
    
    # Revenue stats
    total_revenue = (
        db.query(func.sum(models.Subscription.payment_amount))
        .filter(models.Subscription.payment_status == "completed")
        .scalar() or 0
    )
    
    # Current month revenue
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = (
        db.query(func.sum(models.Subscription.payment_amount))
        .filter(
            models.Subscription.payment_status == "completed",
            models.Subscription.created_at >= current_month_start
        )
        .scalar() or 0
    )
    
    # Usage stats for current month
    monthly_calls = (
        db.query(func.count(models.Usage.id))
        .filter(models.Usage.start_time >= current_month_start)
        .scalar()
    )
    
    monthly_duration = (
        db.query(func.sum(models.Usage.duration))
        .filter(models.Usage.start_time >= current_month_start)
        .scalar() or 0
    )
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
        },
        "plans": {
            "total": total_plans,
        },
        "subscriptions": {
            "total": total_subscriptions,
            "active": active_subscriptions,
            "expired": total_subscriptions - active_subscriptions,
        },
        "usage": {
            "total_records": total_usage_records,
            "monthly_calls": monthly_calls,
            "monthly_duration_hours": round(float(monthly_duration) / 3600, 2),
        },
        "revenue": {
            "total": float(total_revenue),
            "monthly": float(monthly_revenue),
        },
    }


@router.get("/stats/growth")
def read_growth_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get growth statistics for the last 12 months
    """
    now = datetime.utcnow()
    twelve_months_ago = now - timedelta(days=365)
    
    # Monthly user registrations
    monthly_users = (
        db.query(
            func.extract('year', models.User.created_at).label('year'),
            func.extract('month', models.User.created_at).label('month'),
            func.count(models.User.id).label('count')
        )
        .filter(models.User.created_at >= twelve_months_ago)
        .group_by(
            func.extract('year', models.User.created_at),
            func.extract('month', models.User.created_at)
        )
        .order_by(
            func.extract('year', models.User.created_at),
            func.extract('month', models.User.created_at)
        )
        .all()
    )
    
    # Monthly subscriptions
    monthly_subscriptions = (
        db.query(
            func.extract('year', models.Subscription.created_at).label('year'),
            func.extract('month', models.Subscription.created_at).label('month'),
            func.count(models.Subscription.id).label('count'),
            func.sum(models.Subscription.payment_amount).label('revenue')
        )
        .filter(
            models.Subscription.created_at >= twelve_months_ago,
            models.Subscription.payment_status == "completed"
        )
        .group_by(
            func.extract('year', models.Subscription.created_at),
            func.extract('month', models.Subscription.created_at)
        )
        .order_by(
            func.extract('year', models.Subscription.created_at),
            func.extract('month', models.Subscription.created_at)
        )
        .all()
    )
    
    # Monthly usage
    monthly_usage = (
        db.query(
            func.extract('year', models.Usage.start_time).label('year'),
            func.extract('month', models.Usage.start_time).label('month'),
            func.count(models.Usage.id).label('calls'),
            func.sum(models.Usage.duration).label('duration')
        )
        .filter(models.Usage.start_time >= twelve_months_ago)
        .group_by(
            func.extract('year', models.Usage.start_time),
            func.extract('month', models.Usage.start_time)
        )
        .order_by(
            func.extract('year', models.Usage.start_time),
            func.extract('month', models.Usage.start_time)
        )
        .all()
    )
    
    return {
        "monthly_users": [
            {
                "year": int(row.year),
                "month": int(row.month),
                "count": row.count
            }
            for row in monthly_users
        ],
        "monthly_subscriptions": [
            {
                "year": int(row.year),
                "month": int(row.month),
                "count": row.count,
                "revenue": float(row.revenue or 0)
            }
            for row in monthly_subscriptions
        ],
        "monthly_usage": [
            {
                "year": int(row.year),
                "month": int(row.month),
                "calls": row.calls,
                "duration_hours": round(float(row.duration or 0) / 3600, 2)
            }
            for row in monthly_usage
        ],
    }
