from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users (Admin only)
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/with-stats")
def read_users_with_stats(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by email or name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users with subscription and usage statistics (Admin only)
    """
    users = crud.user.get_users_with_stats(
        db, skip=skip, limit=limit, search=search, is_active=is_active
    )
    return users


@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user (Admin only)
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update own user
    """
    current_user_data = {}
    if password is not None:
        current_user_data["password"] = password
    if full_name is not None:
        current_user_data["full_name"] = full_name
    if email is not None:
        current_user_data["email"] = email
    user = crud.user.update(db, db_obj=current_user, obj_in=current_user_data)
    return user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user
    """
    return current_user


@router.get("/me/dashboard")
def read_user_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's dashboard data
    """
    dashboard_data = crud.user.get_user_dashboard_stats(db, user_id=current_user.id)
    return dashboard_data


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.get("/{user_id}/dashboard")
def read_user_dashboard_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get user's dashboard data by ID (Admin only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    dashboard_data = crud.user.get_user_dashboard_stats(db, user_id=user_id)
    return dashboard_data


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user (Admin only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a user (Admin only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=400, detail="Users cannot delete themselves"
        )
    user = crud.user.remove(db, id=user_id)
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
def activate_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Activate a user (Admin only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_update = {"is_active": True}
    user = crud.user.update(db, db_obj=user, obj_in=user_update)
    return {"message": "User activated successfully", "user": user}


@router.post("/{user_id}/deactivate")
def deactivate_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Deactivate a user (Admin only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=400, detail="Users cannot deactivate themselves"
        )
    
    user_update = {"is_active": False}
    user = crud.user.update(db, db_obj=user, obj_in=user_update)
    return {"message": "User deactivated successfully", "user": user}
