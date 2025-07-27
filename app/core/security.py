from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from app.models.user import User
from app.models.admin import Admin
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select


load_dotenv()


SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
USER_ACCESS_TOKEN_EXPIRE_DAYS = os.environ.get("USER_ACCESS_TOKEN_EXPIRE_DAYS")
ADMIN_ACCESS_TOKEN_EXPIRE_DAYS = os.environ.get("ADMIN_ACCESS_TOKEN_EXPIRE_DAYS")

def create_user_access_token(id: int, iat: str):
    expire = datetime.now(timezone.utc) + timedelta(days=int(USER_ACCESS_TOKEN_EXPIRE_DAYS))
    
    # تحويل iat من string إلى unix timestamp للـ JWT
    iat_timestamp = int(datetime.fromisoformat(iat).timestamp())
    
    payload = {
        "id": id,
        "role": "user",
        "iat": iat_timestamp,
        "login_time": iat,
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_user_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        login_time = payload.get("login_time")

        if user_id is None or login_time is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # تحويل login_time (string) إلى unix timestamp
        login_time_unix = int(datetime.fromisoformat(login_time).timestamp())
        
        # تحويل last_login (string) إلى unix timestamp  
        last_login_unix = int(datetime.fromisoformat(user.last_login).timestamp())
        
        # مقارنة unix timestamps
        if login_time_unix < last_login_unix:
            raise HTTPException(status_code=401, detail="Token revoked")

        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized")
    except (ValueError, TypeError) as e:
        # معالجة أخطاء تحليل التاريخ
        raise HTTPException(status_code=401, detail="Unauthorized")





def create_admin_access_token(admin: Admin):
    expire = datetime.now(timezone.utc) + timedelta(days=int(ADMIN_ACCESS_TOKEN_EXPIRE_DAYS))
    payload = {
        "id": admin.id,
        "role": admin.role,
        "admin_level": admin.admin_level,
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: int = payload.get("id")
        admin_role = payload.get("role")
        admin_level = int(payload.get("admin_level"),0)
        if admin_id is None or payload.get("admin_level") is None or payload.get("role") is None or admin_role != "admin" or admin_level < 1:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    


def iso_to_datetime(iso_str: str) -> datetime:
    """
    Convert ISO 8601 datetime string to a datetime object (UTC).
    """
    return datetime.fromisoformat(iso_str)

def iso_to_unix(iso_str: str) -> int:
    """
    Convert ISO 8601 datetime string to Unix timestamp (UTC).
    """
    dt = datetime.fromisoformat(iso_str)
    return int(dt.timestamp())