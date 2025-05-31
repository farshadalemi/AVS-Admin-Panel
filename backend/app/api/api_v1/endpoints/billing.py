from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/invoices/me")
def read_my_invoices(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's billing history (invoices from subscriptions)
    """
    subscriptions = crud.subscription.get_user_subscriptions(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    
    invoices = []
    for subscription in subscriptions:
        if subscription.payment_status == "completed":
            invoices.append({
                "id": f"INV-{subscription.id}",
                "subscription_id": subscription.id,
                "amount": subscription.payment_amount,
                "payment_method": subscription.payment_method,
                "payment_id": subscription.payment_id,
                "payment_date": subscription.created_at,
                "plan_name": subscription.plan.name,
                "period_start": subscription.start_date,
                "period_end": subscription.end_date,
                "status": subscription.payment_status,
            })
    
    return invoices


@router.get("/invoices")
def read_all_invoices(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get all invoices with filters (Admin only)
    """
    subscriptions = crud.subscription.get_subscriptions_with_details(
        db,
        skip=skip,
        limit=limit,
        user_email=user_email,
        payment_status=payment_status
    )
    
    # Filter by date if provided
    if start_date or end_date:
        filtered_subscriptions = []
        for sub in subscriptions:
            sub_date = sub["created_at"]
            if isinstance(sub_date, str):
                sub_date = datetime.fromisoformat(sub_date.replace('Z', '+00:00'))
            
            if start_date and sub_date < start_date:
                continue
            if end_date and sub_date > end_date:
                continue
            
            filtered_subscriptions.append(sub)
        subscriptions = filtered_subscriptions
    
    invoices = []
    for subscription in subscriptions:
        invoices.append({
            "id": f"INV-{subscription['id']}",
            "subscription_id": subscription["id"],
            "amount": subscription["payment_amount"],
            "payment_method": subscription["payment_method"],
            "payment_id": subscription["payment_id"],
            "payment_date": subscription["created_at"],
            "plan_name": subscription["plan"]["name"],
            "period_start": subscription["start_date"],
            "period_end": subscription["end_date"],
            "status": subscription["payment_status"],
            "user": subscription["user"],
        })
    
    return invoices


@router.get("/revenue/summary")
def read_revenue_summary(
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for revenue calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for revenue calculation"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get revenue summary with detailed breakdown (Admin only)
    """
    revenue_stats = crud.subscription.get_revenue_stats(
        db, start_date=start_date, end_date=end_date
    )
    
    # Get additional metrics
    now = datetime.utcnow()
    
    # Current month revenue
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_revenue = crud.subscription.get_revenue_stats(
        db, start_date=current_month_start, end_date=now
    )
    
    # Previous month revenue for comparison
    if current_month_start.month == 1:
        prev_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
    else:
        prev_month_start = current_month_start.replace(month=current_month_start.month - 1)
    
    prev_month_end = current_month_start
    prev_month_revenue = crud.subscription.get_revenue_stats(
        db, start_date=prev_month_start, end_date=prev_month_end
    )
    
    # Calculate growth
    current_revenue = current_month_revenue["total_revenue"]
    prev_revenue = prev_month_revenue["total_revenue"]
    
    growth_rate = 0
    if prev_revenue > 0:
        growth_rate = ((current_revenue - prev_revenue) / prev_revenue) * 100
    
    return {
        "total_revenue": revenue_stats["total_revenue"],
        "total_subscriptions": revenue_stats["total_subscriptions"],
        "average_revenue_per_subscription": revenue_stats["average_revenue_per_subscription"],
        "plan_breakdown": revenue_stats["plan_breakdown"],
        "current_month": {
            "revenue": current_revenue,
            "subscriptions": current_month_revenue["total_subscriptions"],
        },
        "previous_month": {
            "revenue": prev_revenue,
            "subscriptions": prev_month_revenue["total_subscriptions"],
        },
        "growth": {
            "revenue_growth_rate": round(growth_rate, 2),
            "revenue_difference": current_revenue - prev_revenue,
        },
    }


@router.get("/payment-methods")
def read_payment_methods_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get payment methods statistics (Admin only)
    """
    from sqlalchemy import func
    
    payment_stats = (
        db.query(
            models.Subscription.payment_method,
            func.count(models.Subscription.id).label('count'),
            func.sum(models.Subscription.payment_amount).label('total_amount')
        )
        .filter(models.Subscription.payment_status == "completed")
        .group_by(models.Subscription.payment_method)
        .all()
    )
    
    result = []
    for stat in payment_stats:
        result.append({
            "payment_method": stat.payment_method or "Unknown",
            "transaction_count": stat.count,
            "total_amount": float(stat.total_amount or 0),
        })
    
    return result


@router.get("/failed-payments")
def read_failed_payments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get failed payment attempts (Admin only)
    """
    failed_subscriptions = crud.subscription.get_subscriptions_with_details(
        db,
        skip=skip,
        limit=limit,
        payment_status="failed"
    )
    
    return failed_subscriptions


@router.get("/pending-payments")
def read_pending_payments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get pending payment attempts (Admin only)
    """
    pending_subscriptions = crud.subscription.get_subscriptions_with_details(
        db,
        skip=skip,
        limit=limit,
        payment_status="pending"
    )
    
    return pending_subscriptions


@router.post("/process-payment")
def process_payment(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    payment_method: str,
    payment_token: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Process a payment for a subscription (Placeholder for payment gateway integration)
    """
    # Check if plan exists and is active
    plan = crud.plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="Plan is not active")
    
    # Check if user already has an active subscription
    existing_subscription = crud.subscription.get_user_active_subscription(
        db, user_id=current_user.id
    )
    if existing_subscription:
        raise HTTPException(
            status_code=400,
            detail="User already has an active subscription"
        )
    
    # TODO: Integrate with actual payment gateway (Stripe, PayPal, etc.)
    # For now, we'll simulate a successful payment
    
    payment_id = f"pay_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
    
    # Create subscription with completed payment
    subscription_data = schemas.SubscriptionCreate(
        user_id=current_user.id,
        plan_id=plan_id,
        payment_amount=plan.price,
        payment_method=payment_method,
        payment_id=payment_id,
        payment_status="completed",
        is_active=True,
    )
    
    subscription = crud.subscription.create(db, obj_in=subscription_data)
    
    return {
        "message": "Payment processed successfully",
        "subscription": subscription,
        "payment_id": payment_id,
    }


@router.post("/refund/{subscription_id}")
def process_refund(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    refund_amount: Optional[float] = None,
    reason: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Process a refund for a subscription (Admin only)
    """
    subscription = crud.subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.payment_status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Can only refund completed payments"
        )
    
    # TODO: Integrate with actual payment gateway for refund processing
    # For now, we'll simulate a successful refund
    
    refund_amount = refund_amount or subscription.payment_amount
    
    # Update subscription status
    subscription_update = {
        "payment_status": "refunded",
        "is_active": False,
    }
    
    subscription = crud.subscription.update(
        db, db_obj=subscription, obj_in=subscription_update
    )
    
    return {
        "message": "Refund processed successfully",
        "subscription": subscription,
        "refund_amount": refund_amount,
        "reason": reason,
    }


@router.get("/export/invoices")
def export_invoices(
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    format: str = Query("csv", description="Export format (csv, xlsx)"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Export invoices to CSV or Excel (Admin only)
    """
    # TODO: Implement actual file export functionality
    # This would typically generate a file and return a download link
    
    subscriptions = crud.subscription.get_subscriptions_with_details(
        db, skip=0, limit=10000  # Large limit for export
    )
    
    # Filter by date if provided
    if start_date or end_date:
        filtered_subscriptions = []
        for sub in subscriptions:
            sub_date = sub["created_at"]
            if isinstance(sub_date, str):
                sub_date = datetime.fromisoformat(sub_date.replace('Z', '+00:00'))
            
            if start_date and sub_date < start_date:
                continue
            if end_date and sub_date > end_date:
                continue
            
            filtered_subscriptions.append(sub)
        subscriptions = filtered_subscriptions
    
    return {
        "message": f"Export prepared with {len(subscriptions)} records",
        "format": format,
        "record_count": len(subscriptions),
        "download_url": f"/api/v1/billing/download/invoices_{datetime.utcnow().strftime('%Y%m%d')}.{format}",
        # TODO: Return actual download URL
    }
