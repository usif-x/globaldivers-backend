from typing import List, Optional

from pydantic import BaseModel, Field

from datetime import datetime


class Notification(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool = False
    type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: str


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    is_read: Optional[bool] = None


class NotificationList(BaseModel):
    notifications: List[Notification]
