# app/schemas/coupon.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    activity: str = Field(default="all")  # trip, course, all
    discount_percentage: float = Field(..., gt=0, le=100)  # 0 < discount <= 100
    can_used_up_to: int = Field(default=100, ge=1)
    expire_date: Optional[datetime] = None


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    activity: Optional[str] = None
    discount_percentage: Optional[float] = Field(None, gt=0, le=100)
    can_used_up_to: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    expire_date: Optional[datetime] = None


class CouponResponse(BaseModel):
    id: int
    code: str
    activity: str
    discount_percentage: float
    can_used_up_to: int
    used_count: int
    remaining: int
    can_used: bool
    is_active: bool
    expire_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CouponDetailResponse(CouponResponse):
    users: List[dict] = []  # List of users who used the coupon

    class Config:
        from_attributes = True


class ApplyCouponRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)


class ApplyCouponResponse(BaseModel):
    success: bool
    message: str
    coupon: Optional[CouponResponse] = None
