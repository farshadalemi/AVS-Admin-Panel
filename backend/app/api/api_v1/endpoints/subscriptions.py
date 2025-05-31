from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/")
def read_subscriptions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    plan_name: Optional[str] = Query(None, description="Filter by plan name"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve subscriptions with filters (Admin only)
    """
    subscriptions = crud.subscription.get_subscriptions_with_details(
        db, 
        skip=skip, 
        limit=limit,
        user_email=user_email,
        plan_name=plan_name,
        payment_status=payment_status,
        is_active=is_active
    )
    return subscriptions


@router.get("/me")
def read_my_subscriptions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's subscriptions
    """
    subscriptions = crud.subscription.get_user_subscriptions(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return subscriptions


@router.get("/me/active")
def read_my_active_subscription(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's active subscription
    """
    subscription = crud.subscription.get_user_active_subscription(
        db, user_id=current_user.id
    )
    if not subscription:
        return {"message": "No active subscription found"}
    return subscription


@router.post("/", response_model=schemas.Subscription)
def create_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_in: schemas.SubscriptionCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new subscription (User can create for themselves, Admin can create for any user)
    """
    # If not admin, user can only create subscription for themselves
    if not crud.user.is_superuser(current_user) and subscription_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create subscription for another user"
        )
    
    # Check if user exists
    user = crud.user.get(db, id=subscription_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if plan exists and is active
    plan = crud.plan.get(db, id=subscription_in.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="Plan is not active")
    
    # Check if user already has an active subscription
    existing_subscription = crud.subscription.get_user_active_subscription(
        db, user_id=subscription_in.user_id
    )
    if existing_subscription:
        raise HTTPException(
            status_code=400,
            detail="User already has an active subscription"
        )
    
    subscription = crud.subscription.create(db, obj_in=subscription_in)
    return subscription


@router.get("/expiring")
def read_expiring_subscriptions(
    db: Session = Depends(deps.get_db),
    days_ahead: int = Query(7, description="Days ahead to check for expiring subscriptions"),
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get subscriptions expiring within specified days (Admin only)
    """
    subscriptions = crud.subscription.get_expiring_subscriptions(
        db, days_ahead=days_ahead, limit=limit
    )
    return subscriptions


@router.get("/analytics")
def read_subscription_analytics(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get subscription analytics (Admin only)
    """
    analytics = crud.subscription.get_subscription_analytics(db)
    return analytics


@router.get("/revenue")
def read_revenue_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for revenue calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for revenue calculation"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get revenue statistics for a date range (Admin only)
    """
    revenue_stats = crud.subscription.get_revenue_stats(
        db, start_date=start_date, end_date=end_date
    )
    return revenue_stats


@router.get("/{subscription_id}", response_model=schemas.Subscription)
def read_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get subscription by ID
    """
    subscription = crud.subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Users can only view their own subscriptions, admins can view all
    if not crud.user.is_superuser(current_user) and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view this subscription"
        )
    
    return subscription


@router.put("/{subscription_id}", response_model=schemas.Subscription)
def update_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    subscription_in: schemas.SubscriptionUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a subscription (Admin only)
    """
    subscription = crud.subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription = crud.subscription.update(db, db_obj=subscription, obj_in=subscription_in)
    return subscription


@router.post("/{subscription_id}/cancel")
def cancel_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Cancel a subscription (User can cancel their own, Admin can cancel any)
    """
    subscription = crud.subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Users can only cancel their own subscriptions, admins can cancel any
    if not crud.user.is_superuser(current_user) and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to cancel this subscription"
        )
    
    subscription = crud.subscription.cancel_subscription(db, subscription_id=subscription_id)
    return {"message": "Subscription cancelled successfully", "subscription": subscription}


@router.post("/{subscription_id}/renew")
def renew_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    payment_amount: float,
    payment_id: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Renew a subscription (User can renew their own, Admin can renew any)
    """
    subscription = crud.subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Users can only renew their own subscriptions, admins can renew any
    if not crud.user.is_superuser(current_user) and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to renew this subscription"
        )
    
    subscription = crud.subscription.renew_subscription(
        db, subscription_id=subscription_id, payment_amount=payment_amount, payment_id=payment_id
    )
    return {"message": "Subscription renewed successfully", "subscription": subscription}
