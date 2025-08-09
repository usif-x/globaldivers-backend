from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.core.hashing import hash_password, verify_password
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserUpdatePassword
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationList
from datetime import datetime
from app.models.notification import Notification


class UserServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def get_user_by_id(self, id: int) -> UserResponse:
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if not user:
            raise HTTPException(404, detail="user not found")
        else:
            return UserResponse.model_validate(user, from_attributes=True)

    @db_exception_handler
    def update_user(self, user: UserUpdate, id: int):
        stmt = select(User).where(User.id == id)
        updated_user = self.db.execute(stmt).scalars().first()
        if updated_user:
            data = user.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(updated_user, field, value)
            self.db.commit()
            self.db.refresh(updated_user)
            return {
                "success": True,
                "message": "User Updated successfuly",
                "user": UserResponse.model_validate(updated_user, from_attributes=True),
            }
        else:
            raise HTTPException(404, detail="user not found")

    @db_exception_handler
    def update_user_password(self, user: UserUpdatePassword, id: int):
        stmt = select(User).where(User.id == id)
        updated_user = self.db.execute(stmt).scalars().first()
        if not updated_user:
            raise HTTPException(404, detail="User not found")
        if verify_password(user.old_password, updated_user.password):
            updated_user.password = hash_password(user.new_password)
            updated_user.last_login = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(updated_user)
            return {
                "success": True,
                "message": "Password Updated successfuly",
                "user": UserResponse.model_validate(updated_user, from_attributes=True),
            }
        else:
            raise HTTPException(400, detail="Invalid cerdentials")

    @db_exception_handler
    def delete_my_account(self, id: int):
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            self.db.delete(user)
            self.db.commit()
            return {"success": True, "message": "Account deleted successfully"}
        else:
            raise HTTPException(404, detail="An error occured")

    @db_exception_handler
    def get_my_testimonials(self, id: int):
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.testimonials
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def get_my_subscribed_courses(self, id: int):
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.subscribed_courses
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def get_my_invoices(self, user: User):
        stmt = select(User).where(User.id == user.id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.invoices
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def get_my_invoice_by_id(self, id: int, user: User):
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        invoice = next((inv for inv in user.invoices if inv.id == id), None)
        if not invoice:
            raise HTTPException(
                status_code=404, detail="Invoice not found for this user."
            )
        return invoice

    @db_exception_handler
    def get_my_notifications(self, user: User):
        stmt = select(User).where(User.id == user.id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.notifications
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def get_my_notifications_by_id(self, id: int, user: User):
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        notification = next((noti for noti in user.notifications if noti.id == id), None)
        if not notification:
            raise HTTPException(
                status_code=404, detail="Notification not found for this user."
            )
        return notification

    @db_exception_handler
    def add_notification(self, user: User, notification: NotificationCreate):
        user.notifications.append(notification)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return notification

    @db_exception_handler
    def update_notification(self, user: User, id: int, notification: NotificationUpdate):
        stmt = select(Notification).where(
            Notification.user_id == user.id,
            Notification.id == id
        )
        notification = self.db.execute(stmt).scalars().first()
        if not notification:
            raise HTTPException(
                status_code=404, detail="Notification not found for this user."
            )
        notification.title = notification.title or notification.title
        notification.message = notification.message or notification.message
        notification.type = notification.type or notification.type
        notification.is_read = notification.is_read or notification.is_read
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return notification

    @db_exception_handler
    def delete_notification(self, user: User, id: int):
        notification = next((noti for noti in user.notifications if noti.id == id), None)
        if not notification:
            raise HTTPException(
                status_code=404, detail="Notification not found for this user."
            )
        user.notifications.remove(notification)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return notification
