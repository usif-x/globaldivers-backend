import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
)
from app.services.anthropic_client import run_chat_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    from app.core.security import verify_user_token

    try:
        token = auth.split(" ", 1)[1]
        payload = verify_user_token(token, db)
        user_id = payload.get("id")
        if user_id is None:
            return None
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalars().first()
        if user and user.is_active and not user.is_blocked:
            return user
    except Exception:
        return None
    return None


def _get_or_create_session(
    db: Session, session_id: Optional[str], user: Optional[User]
) -> ChatSession:
    if session_id:
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        session = db.execute(stmt).scalars().first()
        if session:
            if not _session_belongs_to_user(session, user):
                raise HTTPException(
                    status_code=403, detail="Session belongs to another user"
                )
            session.last_active_at = datetime.now(timezone.utc)
            if user and session.user_id is None:
                session.user_id = user.id
            db.commit()
            db.refresh(session)
            return session
    new_session = ChatSession(
        user_id=user.id if user else None,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def _session_belongs_to_user(session: ChatSession, user: Optional[User]) -> bool:
    if session.user_id is None:
        return True
    if user and session.user_id == user.id:
        return True
    return False


@router.post("/message", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat_message(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(_get_optional_user),
):
    session = _get_or_create_session(db, body.session_id, user)

    db.add(
        ChatMessage(
            session_id=session.id,
            role="user",
            content=body.message,
        )
    )
    db.commit()

    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .limit(50)
    )
    history_rows = db.execute(history_stmt).scalars().all()

    messages_for_ai = [{"role": m.role, "content": m.content} for m in history_rows]

    reply = await run_chat_turn(
        messages=messages_for_ai,
        auth_user_id=user.id if user else None,
        db=db,
    )

    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=reply,
        )
    )
    db.commit()

    return ChatResponse(session_id=session.id, reply=reply)


@router.post("/message/stream")
@limiter.limit("30/minute")
async def chat_message_stream(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(_get_optional_user),
):
    session = _get_or_create_session(db, body.session_id, user)

    db.add(
        ChatMessage(
            session_id=session.id,
            role="user",
            content=body.message,
        )
    )
    db.commit()

    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .limit(50)
    )
    history_rows = db.execute(history_stmt).scalars().all()

    messages_for_ai = [{"role": m.role, "content": m.content} for m in history_rows]

    reply = await run_chat_turn(
        messages=messages_for_ai,
        auth_user_id=user.id if user else None,
        db=db,
    )

    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=reply,
        )
    )
    db.commit()

    async def event_stream():
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session.id})}\n\n"
        words = reply.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/session/{session_id}/history",
    response_model=ChatSessionResponse,
)
async def get_chat_history(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(_get_optional_user),
):
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    session = db.execute(stmt).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not _session_belongs_to_user(session, user):
        raise HTTPException(status_code=403, detail="Access denied")

    msg_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = db.execute(msg_stmt).scalars().all()

    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        created_at=session.created_at,
        last_active_at=session.last_active_at,
        messages=[
            ChatMessageResponse.model_validate(m, from_attributes=True)
            for m in messages
        ],
    )
