from typing import List

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.public_notification import (
    PublicNotification,
    PublicNotificationCreate,
    PublicNotificationUpdate,
)
from app.services.public_notification import PublicNotificationServices

public_notification_routes = APIRouter(
    prefix="/public-notifications", tags=["Public Notification Endpoints"]
)


@public_notification_routes.post(
    "/", response_model=PublicNotification, dependencies=[Depends(get_current_admin)]
)
async def create_notification(
    notification: PublicNotificationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new public notification (Admin only).
    """
    return PublicNotificationServices(db).create_notification(notification)


@public_notification_routes.get("/", response_model=List[PublicNotification])
async def get_all_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get all public notifications.
    """
    return PublicNotificationServices(db).get_all_notifications(skip=skip, limit=limit)


@public_notification_routes.get("/{notification_id}", response_model=PublicNotification)
async def get_notification_by_id(
    notification_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """
    Get a specific public notification by ID.
    """
    return PublicNotificationServices(db).get_notification_by_id(notification_id)


@public_notification_routes.put(
    "/{notification_id}",
    response_model=PublicNotification,
    dependencies=[Depends(get_current_admin)],
)
async def update_notification(
    notification_id: int = Path(..., ge=1),
    notification: PublicNotificationUpdate = None,
    db: Session = Depends(get_db),
):
    """
    Update a public notification (Admin only).
    """
    return PublicNotificationServices(db).update_notification(
        notification_id, notification
    )


@public_notification_routes.delete(
    "/{notification_id}", dependencies=[Depends(get_current_admin)]
)
async def delete_notification(
    notification_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """
    Delete a public notification (Admin only).
    """
    return PublicNotificationServices(db).delete_notification(notification_id)
