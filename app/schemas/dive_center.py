from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class DayWorkingHours(BaseModel):
    start: str
    end: str
    is_open: bool


class DiveCenterBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=10000)
    images: List[str] = Field(default_factory=list)
    is_image_list: bool = False
    location: str = Field(..., max_length=255)
    hotel_name: Optional[str] = Field(None, max_length=255)
    phone: str = Field(..., max_length=30)
    email: EmailStr
    working_hours: Optional[Dict[str, DayWorkingHours]] = Field(
        default_factory=lambda: {
            "monday": {"start": "09:00", "end": "17:00", "is_open": True},
            "tuesday": {"start": "09:00", "end": "17:00", "is_open": True},
            "wednesday": {"start": "09:00", "end": "17:00", "is_open": True},
            "thursday": {"start": "09:00", "end": "17:00", "is_open": True},
            "friday": {"start": "09:00", "end": "17:00", "is_open": True},
            "saturday": {"start": "10:00", "end": "14:00", "is_open": True},
            "sunday": {"start": "", "end": "", "is_open": False},
        }
    )


class DiveCenterCreate(DiveCenterBase):
    pass


class DiveCenterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    is_image_list: Optional[bool] = None
    location: Optional[str] = None
    hotel_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    working_hours: Optional[Dict[str, DayWorkingHours]] = None


class DiveCenterResponse(DiveCenterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
