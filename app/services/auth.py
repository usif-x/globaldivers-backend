from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.core.hashing import hash_password, verify_password
from app.core.mailer import send_email
from app.core.security import (
    create_admin_access_token,
    create_user_access_token,
    verify_token,
)
from app.core.telegram import notify_admin_login, notify_new_registration
from app.models.admin import Admin
from app.models.user import User
from app.schemas.admin import AdminResponse
from app.schemas.auth import AdminCreate, AdminLogin, UserCreate, UserLogin
from app.schemas.user import UserResponse


class AuthServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_new_user(self, user: UserCreate):
        creation_date = datetime.now(timezone.utc)
        new_user = User(
            full_name=user.full_name,
            password=hash_password(user.password),
            email=user.email,
            last_login=creation_date.isoformat(),
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        token = create_user_access_token(new_user.id, creation_date.isoformat())

        # Send Telegram notification to admins about new user registration
        try:
            notify_new_registration(user.email, user.full_name)
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"Failed to send Telegram notification: {e}")

        # Send welcome email to new user
        try:
            send_email(
                to_email=new_user.email,
                subject="Welcome to Top Divers Hurghada!",
                template_name="welcome_email.html",
                context={"full_name": new_user.full_name},
            )
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"Failed to send welcome email: {e}")

        data = {
            "success": True,
            "message": "User Created Successfully",
            "token": token,
            "token_type": "Bearer",
            "user": UserResponse.model_validate(new_user, from_attributes=True),
        }
        return data

    @db_exception_handler
    def user_login(self, user: UserLogin):
        stmt = select(User).where(User.email == user.email)
        logged_user = self.db.execute(stmt).scalars().first()

        if not logged_user:
            raise HTTPException(400, detail="Invalid credentials")

        if verify_password(user.password, logged_user.password):
            login_date = datetime.now(timezone.utc)
            logged_user.last_login = login_date.isoformat()
            self.db.commit()
            self.db.refresh(logged_user)

            return {
                "success": True,
                "message": "Login Successfully",
                "token": create_user_access_token(
                    logged_user.id, login_date.isoformat()
                ),
                "user": UserResponse.model_validate(logged_user, from_attributes=True),
            }

        raise HTTPException(400, detail="Invalid credentials")

    @db_exception_handler
    def user_logout(self, user_id: int):
        stmt = select(User).where(User.id == user_id)
        logged_user = self.db.execute(stmt).scalars().first()
        logout_date = datetime.now(timezone.utc)
        logged_user.last_login = logout_date.isoformat()
        self.db.commit()
        self.db.refresh(logged_user)
        return {"success": True, "message": "Logout Successfully"}

    @db_exception_handler
    def create_new_admin(self, admin: AdminCreate):
        new_admin = Admin(
            full_name=admin.full_name,
            username=admin.username,
            password=hash_password(admin.password),
            email=admin.email,
            admin_level=admin.admin_level,
            last_login=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        data = {
            "success": True,
            "message": "Admin Created Successfully",
            "admin": AdminResponse.model_validate(new_admin, from_attributes=True),
        }
        return data

    @db_exception_handler
    def admin_login(self, admin: AdminLogin):
        if "@" in admin.username_or_email:
            stmt = select(Admin).where(Admin.email == admin.username_or_email)
        else:
            stmt = select(Admin).where(Admin.username == admin.username_or_email)
        logged_admin = self.db.execute(stmt).scalars().first()
        if not logged_admin:
            raise HTTPException(400, detail="Invalid cerdentials")
        if verify_password(admin.password, logged_admin.password):
            login_date = datetime.now(timezone.utc)
            logged_admin.last_login = login_date.isoformat()
            self.db.commit()
            self.db.refresh(logged_admin)

            # Send Telegram notification about admin login
            try:
                notify_admin_login(
                    logged_admin.username, "Unknown IP"
                )  # You can pass actual IP from request
            except Exception as e:
                # Log the error but don't fail the login
                print(f"Failed to send Telegram notification: {e}")

            data = {
                "success": True,
                "message": "Login Successfully",
                "token": create_admin_access_token(logged_admin),
                "token_type": "Bearer",
                "admin": AdminResponse.model_validate(
                    logged_admin, from_attributes=True
                ),
            }
            return data
        else:
            raise HTTPException(400, detail="Invalid cerdentials")

    def verify_token(self, token: str):
        return verify_token(token)
