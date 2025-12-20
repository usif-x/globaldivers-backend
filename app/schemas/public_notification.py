from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PublicNotification(BaseModel):
    id: int
    title: str
    message: str
    type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class PublicNotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"


class PublicNotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None


class PublicNotificationList(BaseModel):
    notifications: List[PublicNotification]
