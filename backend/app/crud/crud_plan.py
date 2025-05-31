from typing import Any, Dict, Optional, Union, List
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


class CRUDPlan(CRUDBase[Plan, PlanCreate, PlanUpdate]):
    def create(self, db: Session, *, obj_in: PlanCreate) -> Plan:
        # Convert features dict to JSON string if provided
        features_json = None
        if hasattr(obj_in, 'features') and obj_in.features:
            if isinstance(obj_in.features, dict):
                features_json = json.dumps(obj_in.features)
            else:
                features_json = obj_in.features
        
        db_obj = Plan(
            name=obj_in.name,
            description=obj_in.description,
            price=obj_in.price,
            duration_days=obj_in.duration_days,
            max_calls=obj_in.max_calls,
            max_minutes=obj_in.max_minutes,
            features=features_json,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Plan, obj_in: Union[PlanUpdate, Dict[str, Any]]
    ) -> Plan:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle features conversion
        if "features" in update_data and update_data["features"]:
            if isinstance(update_data["features"], dict):
                update_data["features"] = json.dumps(update_data["features"])
        
        update_data["updated_at"] = datetime.utcnow()
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_active_plans(self, db: Session) -> List[Plan]:
        """Get all active plans"""
        return db.query(Plan).filter(Plan.is_active == True).all()

    def get_plan_with_features(self, db: Session, *, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get plan with parsed features"""
        plan = self.get(db, plan_id)
        if not plan:
            return None
        
        features_dict = {}
        if plan.features:
            try:
                features_dict = json.loads(plan.features)
            except json.JSONDecodeError:
                features_dict = {}
        
        return {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "price": plan.price,
            "duration_days": plan.duration_days,
            "max_calls": plan.max_calls,
            "max_minutes": plan.max_minutes,
            "features": features_dict,
            "is_active": plan.is_active,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
        }

    def get_plans_with_stats(self, db: Session) -> List[Dict[str, Any]]:
        """Get all plans with subscription statistics"""
        from app.models.subscription import Subscription
        
        plans = db.query(Plan).all()
        result = []
        
        for plan in plans:
            # Get subscription stats
            total_subscriptions = (
                db.query(func.count(Subscription.id))
                .filter(Subscription.plan_id == plan.id)
                .scalar()
            )
            
            active_subscriptions = (
                db.query(func.count(Subscription.id))
                .filter(
                    Subscription.plan_id == plan.id,
                    Subscription.is_active == True,
                    Subscription.end_date > datetime.utcnow()
                )
                .scalar()
            )
            
            # Calculate total revenue
            total_revenue = (
                db.query(func.sum(Subscription.payment_amount))
                .filter(
                    Subscription.plan_id == plan.id,
                    Subscription.payment_status == "completed"
                )
                .scalar() or 0
            )
            
            features_dict = {}
            if plan.features:
                try:
                    features_dict = json.loads(plan.features)
                except json.JSONDecodeError:
                    features_dict = {}
            
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "price": plan.price,
                "duration_days": plan.duration_days,
                "max_calls": plan.max_calls,
                "max_minutes": plan.max_minutes,
                "features": features_dict,
                "is_active": plan.is_active,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                "stats": {
                    "total_subscriptions": total_subscriptions,
                    "active_subscriptions": active_subscriptions,
                    "total_revenue": float(total_revenue),
                }
            }
            result.append(plan_data)
        
        return result

    def get_by_name(self, db: Session, *, name: str) -> Optional[Plan]:
        """Get plan by name"""
        return db.query(Plan).filter(Plan.name == name).first()

    def deactivate_plan(self, db: Session, *, plan_id: int) -> Optional[Plan]:
        """Deactivate a plan (soft delete)"""
        plan = self.get(db, plan_id)
        if plan:
            plan.is_active = False
            plan.updated_at = datetime.utcnow()
            db.add(plan)
            db.commit()
            db.refresh(plan)
        return plan

    def activate_plan(self, db: Session, *, plan_id: int) -> Optional[Plan]:
        """Activate a plan"""
        plan = self.get(db, plan_id)
        if plan:
            plan.is_active = True
            plan.updated_at = datetime.utcnow()
            db.add(plan)
            db.commit()
            db.refresh(plan)
        return plan

    def get_popular_plans(self, db: Session, *, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most popular plans based on active subscriptions"""
        from app.models.subscription import Subscription
        
        popular_plans = (
            db.query(
                Plan,
                func.count(Subscription.id).label('subscription_count')
            )
            .join(Subscription, Plan.id == Subscription.plan_id)
            .filter(
                Subscription.is_active == True,
                Subscription.end_date > datetime.utcnow(),
                Plan.is_active == True
            )
            .group_by(Plan.id)
            .order_by(func.count(Subscription.id).desc())
            .limit(limit)
            .all()
        )
        
        result = []
        for plan, subscription_count in popular_plans:
            features_dict = {}
            if plan.features:
                try:
                    features_dict = json.loads(plan.features)
                except json.JSONDecodeError:
                    features_dict = {}
            
            result.append({
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "price": plan.price,
                "duration_days": plan.duration_days,
                "max_calls": plan.max_calls,
                "max_minutes": plan.max_minutes,
                "features": features_dict,
                "active_subscriptions": subscription_count,
            })
        
        return result


plan = CRUDPlan(Plan)
