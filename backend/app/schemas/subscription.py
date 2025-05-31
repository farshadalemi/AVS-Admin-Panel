from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import User
from app.schemas.plan import Plan


# Shared properties
class SubscriptionBase(BaseModel):
    user_id: Optional[int] = None
    plan_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = True
    payment_status: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_method: Optional[str] = None
    payment_id: Optional[str] = None


# Properties to receive via API on creation
class SubscriptionCreate(SubscriptionBase):
    user_id: int
    plan_id: int
    payment_amount: float


# Properties to receive via API on update
class SubscriptionUpdate(SubscriptionBase):
    pass


# Properties shared by models stored in DB
class SubscriptionInDBBase(SubscriptionBase):
    id: int
    user_id: int
    plan_id: int
    start_date: datetime
    end_date: datetime
    payment_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class Subscription(SubscriptionInDBBase):
    pass


# Additional properties to return via API with expanded relationships
class SubscriptionWithDetails(Subscription):
    user: Optional[User] = None
    plan: Optional[Plan] = None


# Additional properties stored in DB
class SubscriptionInDB(SubscriptionInDBBase):
    pass
