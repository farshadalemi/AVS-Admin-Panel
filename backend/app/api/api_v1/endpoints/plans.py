from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Plan])
def read_plans(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve plans (Public endpoint for pricing page)
    """
    plans = crud.plan.get_active_plans(db)
    return plans


@router.get("/all")
def read_all_plans(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve all plans including inactive ones (Admin only)
    """
    plans = crud.plan.get_multi(db, skip=skip, limit=limit)
    return plans


@router.get("/with-stats")
def read_plans_with_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve plans with subscription statistics (Admin only)
    """
    plans = crud.plan.get_plans_with_stats(db)
    return plans


@router.get("/popular")
def read_popular_plans(
    db: Session = Depends(deps.get_db),
    limit: int = 5,
) -> Any:
    """
    Get most popular plans based on active subscriptions
    """
    plans = crud.plan.get_popular_plans(db, limit=limit)
    return plans


@router.post("/", response_model=schemas.Plan)
def create_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new plan (Admin only)
    """
    # Check if plan with same name exists
    existing_plan = crud.plan.get_by_name(db, name=plan_in.name)
    if existing_plan:
        raise HTTPException(
            status_code=400,
            detail="A plan with this name already exists.",
        )
    
    plan = crud.plan.create(db, obj_in=plan_in)
    return plan


@router.get("/{plan_id}")
def read_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
) -> Any:
    """
    Get plan by ID with parsed features
    """
    plan = crud.plan.get_plan_with_features(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/{plan_id}", response_model=schemas.Plan)
def update_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: schemas.PlanUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a plan (Admin only)
    """
    plan = crud.plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if updating name to an existing name
    if plan_in.name and plan_in.name != plan.name:
        existing_plan = crud.plan.get_by_name(db, name=plan_in.name)
        if existing_plan:
            raise HTTPException(
                status_code=400,
                detail="A plan with this name already exists.",
            )
    
    plan = crud.plan.update(db, db_obj=plan, obj_in=plan_in)
    return plan


@router.delete("/{plan_id}")
def delete_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a plan (Admin only) - This will deactivate the plan instead of hard delete
    """
    plan = crud.plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if plan has active subscriptions
    from app.models.subscription import Subscription
    from datetime import datetime
    
    active_subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.plan_id == plan_id,
            Subscription.is_active == True,
            Subscription.end_date > datetime.utcnow()
        )
        .count()
    )
    
    if active_subscriptions > 0:
        # Deactivate instead of delete if there are active subscriptions
        plan = crud.plan.deactivate_plan(db, plan_id=plan_id)
        return {"message": f"Plan deactivated due to {active_subscriptions} active subscriptions", "plan": plan}
    else:
        # Hard delete if no active subscriptions
        plan = crud.plan.remove(db, id=plan_id)
        return {"message": "Plan deleted successfully"}


@router.post("/{plan_id}/activate")
def activate_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Activate a plan (Admin only)
    """
    plan = crud.plan.activate_plan(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan activated successfully", "plan": plan}


@router.post("/{plan_id}/deactivate")
def deactivate_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Deactivate a plan (Admin only)
    """
    plan = crud.plan.deactivate_plan(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deactivated successfully", "plan": plan}
