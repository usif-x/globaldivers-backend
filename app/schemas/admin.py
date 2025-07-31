from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
