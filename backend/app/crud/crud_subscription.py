from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.crud.base import CRUDBase
from app.models.subscription import Subscription
from app.models.plan import Plan
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class CRUDSubscription(CRUDBase[Subscription, SubscriptionCreate, SubscriptionUpdate]):
    def create(self, db: Session, *, obj_in: SubscriptionCreate) -> Subscription:
        # Get the plan to calculate end_date
        plan = db.query(Plan).filter(Plan.id == obj_in.plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        
        start_date = obj_in.start_date or datetime.utcnow()
        end_date = obj_in.end_date or (start_date + timedelta(days=plan.duration_days))
        
        db_obj = Subscription(
            user_id=obj_in.user_id,
            plan_id=obj_in.plan_id,
            start_date=start_date,
            end_date=end_date,
            is_active=obj_in.is_active,
            payment_status=obj_in.payment_status or "pending",
            payment_amount=obj_in.payment_amount,
            payment_method=obj_in.payment_method,
            payment_id=obj_in.payment_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Subscription, obj_in: Union[SubscriptionUpdate, Dict[str, Any]]
    ) -> Subscription:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        update_data["updated_at"] = datetime.utcnow()
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_user_active_subscription(self, db: Session, *, user_id: int) -> Optional[Subscription]:
        """Get user's current active subscription"""
        return (
            db.query(Subscription)
            .filter(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.is_active == True,
                    Subscription.end_date > datetime.utcnow()
                )
            )
            .first()
        )

    def get_user_subscriptions(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Subscription]:
        """Get all subscriptions for a user"""
        return (
            db.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .order_by(desc(Subscription.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_subscriptions_with_details(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        user_email: Optional[str] = None,
        plan_name: Optional[str] = None,
        payment_status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get subscriptions with user and plan details"""
        query = (
            db.query(Subscription)
            .join(User, Subscription.user_id == User.id)
            .join(Plan, Subscription.plan_id == Plan.id)
        )
        
        # Apply filters
        if user_email:
            query = query.filter(User.email.ilike(f"%{user_email}%"))
        
        if plan_name:
            query = query.filter(Plan.name.ilike(f"%{plan_name}%"))
        
        if payment_status:
            query = query.filter(Subscription.payment_status == payment_status)
        
        if is_active is not None:
            if is_active:
                query = query.filter(
                    and_(
                        Subscription.is_active == True,
                        Subscription.end_date > datetime.utcnow()
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Subscription.is_active == False,
                        Subscription.end_date <= datetime.utcnow()
                    )
                )
        
        subscriptions = (
            query.order_by(desc(Subscription.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        result = []
        for subscription in subscriptions:
            result.append({
                "id": subscription.id,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "is_active": subscription.is_active,
                "payment_status": subscription.payment_status,
                "payment_amount": subscription.payment_amount,
                "payment_method": subscription.payment_method,
                "payment_id": subscription.payment_id,
                "created_at": subscription.created_at,
                "updated_at": subscription.updated_at,
                "user": {
                    "id": subscription.user.id,
                    "email": subscription.user.email,
                    "full_name": subscription.user.full_name,
                },
                "plan": {
                    "id": subscription.plan.id,
                    "name": subscription.plan.name,
                    "price": subscription.plan.price,
                    "duration_days": subscription.plan.duration_days,
                    "max_calls": subscription.plan.max_calls,
                    "max_minutes": subscription.plan.max_minutes,
                },
                "is_expired": subscription.end_date <= datetime.utcnow(),
                "days_remaining": (subscription.end_date - datetime.utcnow()).days if subscription.end_date > datetime.utcnow() else 0,
            })
        
        return result

    def get_expiring_subscriptions(
        self, db: Session, *, days_ahead: int = 7, limit: int = 100
    ) -> List[Subscription]:
        """Get subscriptions expiring within specified days"""
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        return (
            db.query(Subscription)
            .filter(
                and_(
                    Subscription.is_active == True,
                    Subscription.end_date <= expiry_date,
                    Subscription.end_date > datetime.utcnow()
                )
            )
            .order_by(Subscription.end_date)
            .limit(limit)
            .all()
        )

    def get_revenue_stats(
        self, db: Session, *, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get revenue statistics for a date range"""
        query = db.query(Subscription).filter(Subscription.payment_status == "completed")
        
        if start_date:
            query = query.filter(Subscription.created_at >= start_date)
        if end_date:
            query = query.filter(Subscription.created_at <= end_date)
        
        subscriptions = query.all()
        
        total_revenue = sum(sub.payment_amount for sub in subscriptions)
        total_subscriptions = len(subscriptions)
        
        # Group by plan
        plan_revenue = {}
        for sub in subscriptions:
            plan_name = sub.plan.name
            if plan_name not in plan_revenue:
                plan_revenue[plan_name] = {"count": 0, "revenue": 0}
            plan_revenue[plan_name]["count"] += 1
            plan_revenue[plan_name]["revenue"] += sub.payment_amount
        
        return {
            "total_revenue": total_revenue,
            "total_subscriptions": total_subscriptions,
            "average_revenue_per_subscription": total_revenue / total_subscriptions if total_subscriptions > 0 else 0,
            "plan_breakdown": plan_revenue,
        }

    def cancel_subscription(self, db: Session, *, subscription_id: int) -> Optional[Subscription]:
        """Cancel a subscription"""
        subscription = self.get(db, subscription_id)
        if subscription:
            subscription.is_active = False
            subscription.updated_at = datetime.utcnow()
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
        return subscription

    def renew_subscription(
        self, db: Session, *, subscription_id: int, payment_amount: float, payment_id: Optional[str] = None
    ) -> Optional[Subscription]:
        """Renew a subscription by extending the end date"""
        subscription = self.get(db, subscription_id)
        if subscription:
            plan = subscription.plan
            # Extend from current end_date or now, whichever is later
            new_start = max(subscription.end_date, datetime.utcnow())
            new_end = new_start + timedelta(days=plan.duration_days)
            
            subscription.end_date = new_end
            subscription.is_active = True
            subscription.payment_status = "completed"
            subscription.payment_amount = payment_amount
            subscription.payment_id = payment_id
            subscription.updated_at = datetime.utcnow()
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
        return subscription

    def get_subscription_analytics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive subscription analytics"""
        now = datetime.utcnow()
        
        # Total subscriptions
        total_subscriptions = db.query(func.count(Subscription.id)).scalar()
        
        # Active subscriptions
        active_subscriptions = (
            db.query(func.count(Subscription.id))
            .filter(
                and_(
                    Subscription.is_active == True,
                    Subscription.end_date > now
                )
            )
            .scalar()
        )
        
        # Expired subscriptions
        expired_subscriptions = (
            db.query(func.count(Subscription.id))
            .filter(
                or_(
                    Subscription.is_active == False,
                    Subscription.end_date <= now
                )
            )
            .scalar()
        )
        
        # Monthly revenue (current month)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = (
            db.query(func.sum(Subscription.payment_amount))
            .filter(
                and_(
                    Subscription.payment_status == "completed",
                    Subscription.created_at >= current_month_start
                )
            )
            .scalar() or 0
        )
        
        # Total revenue
        total_revenue = (
            db.query(func.sum(Subscription.payment_amount))
            .filter(Subscription.payment_status == "completed")
            .scalar() or 0
        )
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "monthly_revenue": float(monthly_revenue),
            "total_revenue": float(total_revenue),
            "conversion_rate": (active_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0,
        }


subscription = CRUDSubscription(Subscription)
