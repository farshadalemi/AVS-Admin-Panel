from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import User


# Shared properties
class UsageBase(BaseModel):
    user_id: Optional[int] = None
    call_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: Optional[str] = None
    caller_number: Optional[str] = None
    destination_number: Optional[str] = None
    call_type: Optional[str] = None
    call_summary: Optional[str] = None
    recording_url: Optional[str] = None


# Properties to receive via API on creation
class UsageCreate(UsageBase):
    user_id: int
    call_id: str
    start_time: datetime
    status: str
    caller_number: str
    destination_number: str
    call_type: str


# Properties to receive via API on update
class UsageUpdate(UsageBase):
    pass


# Properties shared by models stored in DB
class UsageInDBBase(UsageBase):
    id: int
    user_id: int
    call_id: str
    start_time: datetime
    status: str
    caller_number: str
    destination_number: str
    call_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class Usage(UsageInDBBase):
    pass


# Additional properties to return via API with expanded relationships
class UsageWithUser(Usage):
    user: Optional[User] = None


# Additional properties stored in DB
class UsageInDB(UsageInDBBase):
    pass
