# app/schemas/chat.py
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ENDED = "ended"


class MessageSender(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SYSTEM = "system"


class MessageType(str, Enum):
    MESSAGE = "message"
    SESSION_CREATED = "session_created"
    NEW_SESSION = "new_session"
    NEW_MESSAGE = "new_message"
    SESSION_ENDED = "session_ended"
    CHAT_CLOSED = "chat_closed"
    INITIAL_SESSIONS = "initial_sessions"


# Request/Response Models
class MessageCreate(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: str
    sender: MessageSender
    text: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    customer_ip: str
    browser: str
    device: str


class SessionResponse(BaseModel):
    id: str
    customer_ip: str
    browser: str
    device: str
    status: SessionStatus
    started_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class SessionWithMessages(SessionResponse):
    messages: List[MessageResponse]


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]


class ChatStatsResponse(BaseModel):
    active_sessions: int
    closed_sessions: int
    ended_sessions: int
    total_sessions: int
    total_messages: int
    connected_admins: int


# WebSocket Message Models
class WSMessageBase(BaseModel):
    type: MessageType


class WSCustomerMessage(WSMessageBase):
    text: str


class WSAdminMessage(WSMessageBase):
    session_id: str
    text: str


class WSSessionCreated(WSMessageBase):
    session_id: str


class WSNewSession(WSMessageBase):
    session: SessionResponse


class WSNewMessage(WSMessageBase):
    session_id: str
    message: MessageResponse


class WSSessionUpdate(WSMessageBase):
    session_id: str


class WSInitialSessions(WSMessageBase):
    sessions: List[SessionResponse]


# Internal Data Models
class ChatMessage:
    def __init__(self, id: str, sender: str, text: str, timestamp: datetime):
        self.id = id
        self.sender = sender
        self.text = text
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
        }


class ChatSession:
    def __init__(self, id: str, customer_ip: str, browser: str, device: str):
        self.id = id
        self.customer_ip = customer_ip
        self.browser = browser
        self.device = device
        self.status = SessionStatus.ACTIVE
        self.started_at = datetime.now()
        self.messages: List[ChatMessage] = []
        self.customer_ws = None

    def to_dict(self):
        return {
            "id": self.id,
            "customer_ip": self.customer_ip,
            "browser": self.browser,
            "device": self.device,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "message_count": len(self.messages),
        }

    def add_message(self, message: ChatMessage):
        self.messages.append(message)

    def close_chat(self):
        self.status = SessionStatus.CLOSED

    def end_session(self):
        self.status = SessionStatus.ENDED
        if self.customer_ws:
            self.customer_ws = None


# Response Models for API endpoints
class CloseSessionResponse(BaseModel):
    message: str
    session_id: str
    status: SessionStatus


class EndSessionResponse(BaseModel):
    message: str
    session_id: str
