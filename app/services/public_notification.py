from typing import List

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.public_notification import PublicNotification
from app.schemas.public_notification import (
    PublicNotification as PublicNotificationSchema,
)
from app.schemas.public_notification import (
    PublicNotificationCreate,
    PublicNotificationUpdate,
)


class PublicNotificationServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_notification(
        self, notification: PublicNotificationCreate
    ) -> PublicNotificationSchema:
        db_notification = PublicNotification(**notification.model_dump())
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)
        return PublicNotificationSchema.model_validate(db_notification)

    @db_exception_handler
    def get_all_notifications(
        self, skip: int = 0, limit: int = 100
    ) -> List[PublicNotificationSchema]:
        stmt = (
            select(PublicNotification)
            .order_by(desc(PublicNotification.created_at))
            .offset(skip)
            .limit(limit)
        )
        notifications = self.db.execute(stmt).scalars().all()
        return [PublicNotificationSchema.model_validate(n) for n in notifications]

    @db_exception_handler
    def get_notification_by_id(self, id: int) -> PublicNotificationSchema:
        stmt = select(PublicNotification).where(PublicNotification.id == id)
        notification = self.db.execute(stmt).scalars().first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return PublicNotificationSchema.model_validate(notification)

    @db_exception_handler
    def update_notification(
        self, id: int, notification_update: PublicNotificationUpdate
    ) -> PublicNotificationSchema:
        stmt = select(PublicNotification).where(PublicNotification.id == id)
        db_notification = self.db.execute(stmt).scalars().first()

        if not db_notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        update_data = notification_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_notification, field, value)

        self.db.commit()
        self.db.refresh(db_notification)
        return PublicNotificationSchema.model_validate(db_notification)

    @db_exception_handler
    def delete_notification(self, id: int):
        stmt = select(PublicNotification).where(PublicNotification.id == id)
        notification = self.db.execute(stmt).scalars().first()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        self.db.delete(notification)
        self.db.commit()
        return {"success": True, "message": "Notification deleted successfully"}
