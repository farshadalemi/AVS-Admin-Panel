from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# Shared properties
class PlanBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    max_calls: Optional[int] = None
    max_minutes: Optional[int] = None
    features: Optional[str] = None
    is_active: Optional[bool] = True


# Properties to receive via API on creation
class PlanCreate(PlanBase):
    name: str
    price: float
    duration_days: int


# Properties to receive via API on update
class PlanUpdate(PlanBase):
    pass


# Properties shared by models stored in DB
class PlanInDBBase(PlanBase):
    id: int
    name: str
    price: float
    duration_days: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class Plan(PlanInDBBase):
    features_dict: Optional[Dict[str, Any]] = None


# Additional properties stored in DB
class PlanInDB(PlanInDBBase):
    pass
