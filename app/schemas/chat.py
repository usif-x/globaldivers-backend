from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: str
    user_id: Optional[int] = None
    created_at: datetime
    last_active_at: datetime
    messages: list[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
