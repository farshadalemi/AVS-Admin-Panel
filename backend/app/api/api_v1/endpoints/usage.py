from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/")
def read_usage_records(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    call_status: Optional[str] = Query(None, description="Filter by call status"),
    call_type: Optional[str] = Query(None, description="Filter by call type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve usage records with filters (Admin only)
    """
    usage_records = crud.usage.get_usage_with_user_details(
        db,
        skip=skip,
        limit=limit,
        user_email=user_email,
        call_status=call_status,
        call_type=call_type,
        start_date=start_date,
        end_date=end_date
    )
    return usage_records


@router.get("/me")
def read_my_usage(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's usage records
    """
    usage_records = crud.usage.get_user_usage(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return usage_records


@router.get("/me/monthly/{year}/{month}")
def read_my_monthly_usage(
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's monthly usage statistics
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    usage_stats = crud.usage.get_user_monthly_usage(
        db, user_id=current_user.id, year=year, month=month
    )
    return usage_stats


@router.get("/analytics")
def read_usage_analytics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get system-wide usage analytics (Admin only)
    """
    analytics = crud.usage.get_system_usage_analytics(
        db, start_date=start_date, end_date=end_date
    )
    return analytics


@router.get("/active-calls")
def read_active_calls(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get currently active calls (Admin only)
    """
    active_calls = crud.usage.get_active_calls(db)
    return active_calls


@router.post("/", response_model=schemas.Usage)
def create_usage_record(
    *,
    db: Session = Depends(deps.get_db),
    usage_in: schemas.UsageCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new usage record (Usually called by IPCC system)
    """
    # If not admin, user can only create usage for themselves
    if not crud.user.is_superuser(current_user) and usage_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create usage record for another user"
        )
    
    # Check if user exists
    user = crud.user.get(db, id=usage_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if call_id already exists
    existing_usage = crud.usage.get_by_call_id(db, call_id=usage_in.call_id)
    if existing_usage:
        raise HTTPException(
            status_code=400,
            detail="Usage record with this call_id already exists"
        )
    
    usage = crud.usage.create(db, obj_in=usage_in)
    return usage


@router.get("/user/{user_id}")
def read_user_usage(
    user_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get usage records for a specific user (Admin only)
    """
    # Check if user exists
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    usage_records = crud.usage.get_user_usage(
        db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return usage_records


@router.get("/user/{user_id}/monthly/{year}/{month}")
def read_user_monthly_usage(
    user_id: int,
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get user's monthly usage statistics (Admin only)
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    # Check if user exists
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    usage_stats = crud.usage.get_user_monthly_usage(
        db, user_id=user_id, year=year, month=month
    )
    return usage_stats


@router.get("/{usage_id}", response_model=schemas.Usage)
def read_usage_record(
    *,
    db: Session = Depends(deps.get_db),
    usage_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get usage record by ID
    """
    usage = crud.usage.get(db, id=usage_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Usage record not found")
    
    # Users can only view their own usage records, admins can view all
    if not crud.user.is_superuser(current_user) and usage.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view this usage record"
        )
    
    return usage


@router.put("/{usage_id}", response_model=schemas.Usage)
def update_usage_record(
    *,
    db: Session = Depends(deps.get_db),
    usage_id: int,
    usage_in: schemas.UsageUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a usage record (Admin only)
    """
    usage = crud.usage.get(db, id=usage_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Usage record not found")
    
    usage = crud.usage.update(db, db_obj=usage, obj_in=usage_in)
    return usage


@router.put("/call/{call_id}/end")
def end_call(
    *,
    db: Session = Depends(deps.get_db),
    call_id: str,
    end_time: datetime,
    duration: float,
    status: str = "completed",
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update call end details (Usually called by IPCC system)
    """
    usage = crud.usage.get_by_call_id(db, call_id=call_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Usage record not found")
    
    # If not admin, user can only update their own usage records
    if not crud.user.is_superuser(current_user) and usage.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update this usage record"
        )
    
    usage = crud.usage.update_call_end(
        db, call_id=call_id, end_time=end_time, duration=duration, status=status
    )
    return {"message": "Call ended successfully", "usage": usage}


@router.delete("/{usage_id}")
def delete_usage_record(
    *,
    db: Session = Depends(deps.get_db),
    usage_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a usage record (Admin only)
    """
    usage = crud.usage.get(db, id=usage_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Usage record not found")
    
    usage = crud.usage.remove(db, id=usage_id)
    return {"message": "Usage record deleted successfully"}
