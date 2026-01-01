# app/schemas/activity_availability.py

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ActivityAvailabilityBase(BaseModel):
    activity_type: str = Field(..., pattern="^(trip|course)$")
    activity_id: int = Field(..., gt=0)
    date: date
    reason: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_future_date(cls, v):
        """Ensure the date is not in the past"""
        if v < date.today():
            raise ValueError("Cannot close activity for past dates")
        return v


class ActivityAvailabilityCreate(ActivityAvailabilityBase):
    """Schema for creating a new availability record (closing an activity)"""

    pass


class ActivityAvailabilityUpdate(BaseModel):
    """Schema for updating an availability record (changing the date)"""

    date: date
    reason: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_future_date(cls, v):
        """Ensure the date is not in the past"""
        if v < date.today():
            raise ValueError("Cannot update to a past date")
        return v


class ActivityAvailabilityResponse(ActivityAvailabilityBase):
    """Schema for returning availability data"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityAvailabilityCheckRequest(BaseModel):
    """Schema for checking if an activity is available"""

    activity_type: str = Field(..., pattern="^(trip|course)$")
    activity_id: int = Field(..., gt=0)
    date: date


class ActivityAvailabilityCheckResponse(BaseModel):
    """Response for availability check"""

    is_available: bool
    reason: Optional[str] = None
    message: str
