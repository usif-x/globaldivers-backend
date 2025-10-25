from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_admin_token, verify_user_token
from app.models.admin import Admin
from app.models.user import User

from .database import get_db


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = auth_header.split(" ")[1]

        # Get the payload from the JWT token
        payload = verify_user_token(token, db)
        user_id = payload.get("id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Define the database query function
        def get_user_from_db():
            stmt = select(User).where(User.id == user_id)
            user = db.execute(stmt).scalars().first()
            return user

        # Run the blocking call in a thread pool
        user = await run_in_threadpool(get_user_from_db)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Inactive user")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Blocked user")

        return user  # This is the User model instance, not the payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


def get_current_admin(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = verify_admin_token(token)
    admin_id = payload.get("id")
    stmt = select(Admin).where(Admin.id == admin_id)
    admin = db.execute(stmt).scalars().first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


def get_current_super_admin(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = auth_header.split(" ")[1]
    payload = verify_admin_token(token)
    admin_id = payload.get("id")
    stmt = select(Admin).where(Admin.id == admin_id)
    admin = db.execute(stmt).scalars().first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if int(admin.admin_level) >= 2:
        return admin
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")


def unix_to_iso(unix_ts: int) -> str:
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()


def iso_to_unix(iso_str: str) -> int:
    dt = datetime.strptime(iso_str, "%Y-%m-%d %H:%M:%S")
    dt = dt.replace(tzinfo=timezone.utc)  # تأكد أنه توقيت UTC
    return int(dt.timestamp())
