# app/services/chat.py
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import WebSocket
from user_agents import parse

from app.schemas.chat import (
    ChatMessage,
    ChatSession,
    ChatStatsResponse,
    MessageResponse,
    MessageSender,
    SessionResponse,
    SessionStatus,
)
from app.utils.json_encoder import json_dumps


class ChatService:
    def __init__(self):
        # In-memory storage (replace with database for production)
        self.sessions: Dict[str, ChatSession] = {}
        self.admin_connections: List[WebSocket] = []

    def get_client_info(self, headers: dict) -> Tuple[str, str]:
        """Extract client information from headers"""
        user_agent_string = headers.get("user-agent", "Unknown")
        user_agent = parse(user_agent_string)

        browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
        device = f"{user_agent.os.family} {user_agent.os.version_string}"

        return browser, device

    def get_client_ip(self, headers: dict) -> str:
        """Get client IP from headers"""
        forwarded = headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return headers.get("x-real-ip", "Unknown")

    async def broadcast_to_admins(self, message: dict):
        """Broadcast message to all connected admins"""
        if not self.admin_connections:
            return

        disconnected = []
        for admin_ws in self.admin_connections:
            try:
                await admin_ws.send_text(json_dumps(message))
            except Exception as e:
                print(f"Failed to send message to admin: {e}")
                disconnected.append(admin_ws)

        # Remove disconnected admins
        for ws in disconnected:
            self.admin_connections.remove(ws)

    def create_session(self, headers: dict) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        browser, device = self.get_client_info(headers)
        client_ip = self.get_client_ip(headers)

        session = ChatSession(
            id=session_id, customer_ip=client_ip, browser=browser, device=device
        )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_active_sessions(self) -> List[ChatSession]:
        """Get all active sessions"""
        return [
            session
            for session in self.sessions.values()
            if session.status in [SessionStatus.ACTIVE, SessionStatus.CLOSED]
        ]

    def add_message(
        self, session_id: str, sender: MessageSender, text: str
    ) -> Optional[ChatMessage]:
        """Add message to session"""
        session = self.get_session(session_id)
        if not session:
            return None

        message = ChatMessage(
            id=str(uuid.uuid4()), sender=sender, text=text, timestamp=datetime.now()
        )

        session.add_message(message)
        return message

    async def handle_customer_message(self, session_id: str, text: str):
        """Handle incoming customer message"""
        message = self.add_message(session_id, MessageSender.CUSTOMER, text)
        if not message:
            return

        # Broadcast to admins
        await self.broadcast_to_admins(
            {
                "type": "new_message",
                "session_id": session_id,
                "message": message.to_dict(),
            }
        )

    async def handle_admin_message(self, session_id: str, text: str) -> bool:
        """Handle incoming admin message"""
        session = self.get_session(session_id)
        if not session or not session.customer_ws:
            return False

        message = self.add_message(session_id, MessageSender.ADMIN, text)
        if not message:
            return False

        # Send to customer
        try:
            await session.customer_ws.send_text(
                json.dumps({"type": "message", "message": message.to_dict()})
            )
        except Exception as e:
            print(f"Failed to send message to customer: {e}")
            return False

        # Broadcast to other admins
        await self.broadcast_to_admins(
            {
                "type": "new_message",
                "session_id": session_id,
                "message": message.to_dict(),
            }
        )

        return True

    async def connect_customer(
        self, websocket: WebSocket, headers: dict
    ) -> ChatSession:
        """Connect customer and create session"""
        session = self.create_session(headers)
        session.customer_ws = websocket

        # Notify admins about new session
        await self.broadcast_to_admins(
            {"type": "new_session", "session": session.to_dict()}
        )

        return session

    async def disconnect_customer(self, session_id: str):
        """Handle customer disconnection"""
        session = self.get_session(session_id)
        if not session:
            return

        session.end_session()

        # Notify admins
        await self.broadcast_to_admins(
            {"type": "session_ended", "session_id": session_id}
        )

    def connect_admin(self, websocket: WebSocket):
        """Connect admin"""
        self.admin_connections.append(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        """Disconnect admin"""
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def close_chat(self, session_id: str) -> bool:
        """Close chat but keep session active"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.close_chat()

        # Notify customer
        if session.customer_ws:
            try:
                await session.customer_ws.send_text(
                    json.dumps(
                        {
                            "type": "chat_closed",
                            "message": "Chat has been closed by admin",
                        }
                    )
                )
            except Exception as e:
                print(f"Failed to notify customer of chat closure: {e}")

        # Notify admins
        await self.broadcast_to_admins(
            {"type": "chat_closed", "session_id": session_id}
        )

        return True

    async def end_session(self, session_id: str) -> bool:
        """End the entire session"""
        session = self.get_session(session_id)
        if not session:
            return False

        # Disconnect customer
        if session.customer_ws:
            try:
                await session.customer_ws.close()
            except Exception as e:
                print(f"Failed to close customer websocket: {e}")

        session.end_session()

        # Notify admins
        await self.broadcast_to_admins(
            {"type": "session_ended", "session_id": session_id}
        )

        return True

    def get_sessions_response(self) -> List[SessionResponse]:
        """Get all sessions formatted for API response"""
        return [
            SessionResponse(**session.to_dict())
            for session in self.get_active_sessions()
        ]

    def get_session_with_messages(self, session_id: str) -> Optional[dict]:
        """Get session with all messages"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session": SessionResponse(**session.to_dict()),
            "messages": [MessageResponse(**msg.to_dict()) for msg in session.messages],
        }

    def get_chat_stats(self) -> ChatStatsResponse:
        """Get chat statistics"""
        active_count = sum(
            1 for s in self.sessions.values() if s.status == SessionStatus.ACTIVE
        )
        closed_count = sum(
            1 for s in self.sessions.values() if s.status == SessionStatus.CLOSED
        )
        ended_count = sum(
            1 for s in self.sessions.values() if s.status == SessionStatus.ENDED
        )
        total_messages = sum(len(s.messages) for s in self.sessions.values())

        return ChatStatsResponse(
            active_sessions=active_count,
            closed_sessions=closed_count,
            ended_sessions=ended_count,
            total_sessions=len(self.sessions),
            total_messages=total_messages,
            connected_admins=len(self.admin_connections),
        )

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old ended sessions (call this periodically)"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if (
                session.status == SessionStatus.ENDED
                and session.started_at.timestamp() < cutoff_time
            ):
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.sessions[session_id]

        return len(sessions_to_remove)


# Create singleton instance
chat_service = ChatService()
