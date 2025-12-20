from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .course import CourseResponse
from .invoice import InvoiceResponse
from .notification import Notification as NotificationResponse
from .testimonial import TestimonialResponse


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[str] = None
    is_active: bool
    is_blocked: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str


class UserUpdateStatus(BaseModel):
    is_active: bool
    is_blocked: bool


class UserFullDetailsResponse(BaseModel):
    user: UserResponse
    testimonials: List[TestimonialResponse]
    invoices: List[InvoiceResponse]
    notifications: List[NotificationResponse]
    subscribed_courses: List[CourseResponse]

    class Config:
        from_attributes = True
