# app/routes/chat.py
import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.schemas.chat import (
    ChatStatsResponse,
    CloseSessionResponse,
    EndSessionResponse,
    SessionListResponse,
    SessionWithMessages,
)
from app.services.chat import chat_service
from app.utils.json_encoder import json_dumps

chat_routes = APIRouter(prefix="/chat", tags=["Live Chat"])


@chat_routes.websocket("/ws/customer")
async def customer_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for customer connections"""
    await websocket.accept()

    # Get client info from headers
    headers = dict(websocket.headers)

    # Create session and connect customer
    session = await chat_service.connect_customer(websocket, headers)

    # Send session info to customer
    await websocket.send_text(
        json.dumps({"type": "session_created", "session_id": session.id})
    )

    try:
        while True:
            # Receive message from customer
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Validate message
            if message_data.get("type") == "message" and "text" in message_data:
                await chat_service.handle_customer_message(
                    session.id, message_data["text"]
                )

    except WebSocketDisconnect:
        # Handle customer disconnection
        await chat_service.disconnect_customer(session.id)
    except Exception as e:
        print(f"Customer WebSocket error: {e}")
        await chat_service.disconnect_customer(session.id)


@chat_routes.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for admin connections"""
    await websocket.accept()

    # Connect admin
    chat_service.connect_admin(websocket)

    # Send current sessions to newly connected admin
    current_sessions = chat_service.get_sessions_response()
    await websocket.send_text(
        json_dumps(
            {
                "type": "initial_sessions",
                "sessions": [session.dict() for session in current_sessions],
            }
        )
    )

    try:
        while True:
            # Receive message from admin
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Validate and handle admin message
            if (
                message_data.get("type") == "message"
                and "session_id" in message_data
                and "text" in message_data
            ):

                success = await chat_service.handle_admin_message(
                    message_data["session_id"], message_data["text"]
                )

                if not success:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Failed to send message. Customer may be disconnected.",
                            }
                        )
                    )

    except WebSocketDisconnect:
        # Handle admin disconnection
        chat_service.disconnect_admin(websocket)
    except Exception as e:
        print(f"Admin WebSocket error: {e}")
        chat_service.disconnect_admin(websocket)


# REST API Endpoints
@chat_routes.get("/sessions", response_model=SessionListResponse)
async def get_sessions():
    """Get all active chat sessions"""
    sessions = chat_service.get_sessions_response()
    return SessionListResponse(sessions=sessions)


@chat_routes.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def get_session_messages(session_id: str):
    """Get messages for a specific session"""
    session_data = chat_service.get_session_with_messages(session_id)

    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Extract session data and flatten it to top level
    session_info = session_data["session"]
    messages = session_data["messages"]

    # Create the response with flattened session data
    response_data = {
        **session_info.dict(),  # Flatten session fields to top level
        "messages": messages,
    }

    return SessionWithMessages(**response_data)


@chat_routes.post(
    "/sessions/{session_id}/close-chat", response_model=CloseSessionResponse
)
async def close_chat(session_id: str):
    """Close chat but keep session active"""
    success = await chat_service.close_chat(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return CloseSessionResponse(
        message="Chat closed successfully", session_id=session_id, status="closed"
    )


@chat_routes.post(
    "/sessions/{session_id}/end-session", response_model=EndSessionResponse
)
async def end_session(session_id: str):
    """End the entire session"""
    success = await chat_service.end_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return EndSessionResponse(
        message="Session ended successfully", session_id=session_id
    )


@chat_routes.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats():
    """Get chat statistics"""
    return chat_service.get_chat_stats()


@chat_routes.delete("/sessions/cleanup")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """Clean up old ended sessions"""
    cleaned_count = chat_service.cleanup_old_sessions(max_age_hours)
    return {
        "message": f"Cleaned up {cleaned_count} old sessions",
        "cleaned_sessions": cleaned_count,
    }


@chat_routes.get("/health")
async def chat_health_check():
    """Health check for chat service"""
    stats = chat_service.get_chat_stats()
    return {
        "status": "healthy",
        "active_sessions": stats.active_sessions,
        "connected_admins": stats.connected_admins,
        "uptime": "ok",
    }
