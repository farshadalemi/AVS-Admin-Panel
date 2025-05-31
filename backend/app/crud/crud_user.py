from typing import Any, Dict, Optional, Union, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        update_data["updated_at"] = datetime.utcnow()
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def get_users_with_stats(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get users with their subscription and usage statistics"""
        from app.models.subscription import Subscription
        from app.models.usage import Usage
        
        query = db.query(User)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        users = query.offset(skip).limit(limit).all()
        
        result = []
        for user in users:
            # Get active subscription
            active_subscription = (
                db.query(Subscription)
                .filter(
                    and_(
                        Subscription.user_id == user.id,
                        Subscription.is_active == True,
                        Subscription.end_date > datetime.utcnow()
                    )
                )
                .first()
            )
            
            # Get usage stats for current month
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            usage_stats = (
                db.query(
                    func.count(Usage.id).label('total_calls'),
                    func.sum(Usage.duration).label('total_duration')
                )
                .filter(
                    and_(
                        Usage.user_id == user.id,
                        Usage.start_time >= current_month_start
                    )
                )
                .first()
            )
            
            user_data = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "active_subscription": {
                    "id": active_subscription.id if active_subscription else None,
                    "plan_name": active_subscription.plan.name if active_subscription else None,
                    "end_date": active_subscription.end_date if active_subscription else None,
                    "payment_status": active_subscription.payment_status if active_subscription else None,
                } if active_subscription else None,
                "current_month_stats": {
                    "total_calls": usage_stats.total_calls or 0,
                    "total_duration": float(usage_stats.total_duration or 0),
                }
            }
            result.append(user_data)
        
        return result

    def get_user_dashboard_stats(self, db: Session, *, user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics for a specific user"""
        from app.models.subscription import Subscription
        from app.models.usage import Usage
        
        user = self.get(db, user_id)
        if not user:
            return {}
        
        # Get active subscription
        active_subscription = (
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
        
        # Get usage stats for different periods
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Current month stats
        current_month_stats = (
            db.query(
                func.count(Usage.id).label('total_calls'),
                func.sum(Usage.duration).label('total_duration')
            )
            .filter(
                and_(
                    Usage.user_id == user_id,
                    Usage.start_time >= current_month_start
                )
            )
            .first()
        )
        
        # All time stats
        all_time_stats = (
            db.query(
                func.count(Usage.id).label('total_calls'),
                func.sum(Usage.duration).label('total_duration')
            )
            .filter(Usage.user_id == user_id)
            .first()
        )
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at,
            },
            "active_subscription": {
                "id": active_subscription.id if active_subscription else None,
                "plan_name": active_subscription.plan.name if active_subscription else None,
                "plan_price": active_subscription.plan.price if active_subscription else None,
                "start_date": active_subscription.start_date if active_subscription else None,
                "end_date": active_subscription.end_date if active_subscription else None,
                "payment_status": active_subscription.payment_status if active_subscription else None,
                "max_calls": active_subscription.plan.max_calls if active_subscription else None,
                "max_minutes": active_subscription.plan.max_minutes if active_subscription else None,
            } if active_subscription else None,
            "current_month_usage": {
                "total_calls": current_month_stats.total_calls or 0,
                "total_duration": float(current_month_stats.total_duration or 0),
                "remaining_calls": (
                    (active_subscription.plan.max_calls - (current_month_stats.total_calls or 0))
                    if active_subscription and active_subscription.plan.max_calls
                    else None
                ),
                "remaining_minutes": (
                    (active_subscription.plan.max_minutes - (float(current_month_stats.total_duration or 0) / 60))
                    if active_subscription and active_subscription.plan.max_minutes
                    else None
                ),
            },
            "all_time_usage": {
                "total_calls": all_time_stats.total_calls or 0,
                "total_duration": float(all_time_stats.total_duration or 0),
            }
        }


user = CRUDUser(User)
