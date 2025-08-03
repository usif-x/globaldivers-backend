from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.user import UserResponse


class AdminResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    role: str
    admin_level: int
    is_active: bool
    last_login: str

    class Config:
        form_attributes = True


class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    admin_level: Optional[int] = None


class AdminUpdatePassword(BaseModel):
    old_password: str
    new_password: str


class PaginatedUsersResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None


class PasswordUpdate(BaseModel):
    password: str


class AdminEnrollmentRequest(BaseModel):
    user_id: int
    course_id: int
