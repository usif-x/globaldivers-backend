from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi_cache.decorator import cache
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    Notification,
    NotificationCreate,
    NotificationList,
    NotificationUpdate,
)
from app.schemas.user import *
from app.services.course import CourseServices
from app.services.user import UserServices

user_routes = APIRouter(prefix="/users", tags=["User Endpoints"])


@user_routes.get("/me")
@cache(expire=600)
async def get_current_user_info(user: User = Depends(get_current_user)):
    # Handle the case where user might be a dict
    if not isinstance(user, User) and isinstance(user, dict) and "id" in user:
        # Fetch the actual user object
        db = next(get_db())
        user_obj = db.query(User).filter(User.id == user["id"]).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user_obj, from_attributes=True)
    return UserResponse.model_validate(user, from_attributes=True)


@user_routes.get("/{id}", response_model=UserResponse)
@cache(expire=600)
async def get_user_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return UserServices(db).get_user_by_id(id)


@user_routes.put("/update")
async def update_user(
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Handle the case where current_user might be a dict
    user_id = (
        current_user.id if isinstance(current_user, User) else current_user.get("id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    return UserServices(db).update_user(user, user_id)


@user_routes.put("/update/password")
async def update_user_password(
    user: UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Handle the case where current_user might be a dict
    user_id = (
        current_user.id if isinstance(current_user, User) else current_user.get("id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    return UserServices(db).update_user_password(user, user_id)


@user_routes.delete("/delete")
async def delete_user(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Handle the case where current_user might be a dict
    user_id = (
        current_user.id if isinstance(current_user, User) else current_user.get("id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    return UserServices(db).delete_my_account(user_id)


@user_routes.get("/me/testimonials")
async def get_my_testimonials(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Handle the case where current_user might be a dict
    user_id = (
        current_user.id if isinstance(current_user, User) else current_user.get("id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    return UserServices(db).get_my_testimonials(user_id)


@user_routes.get("/me/courses")
async def get_my_subscribed_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Handle the case where current_user might be a dict
    user_id = (
        current_user.id if isinstance(current_user, User) else current_user.get("id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")
    return UserServices(db).get_my_subscribed_courses(user_id)


@user_routes.get("/me/invoices")
async def get_my_invoices(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # If current_user is a dict, fetch the actual User object
    if (
        not isinstance(current_user, User)
        and isinstance(current_user, dict)
        and "id" in current_user
    ):
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserServices(db).get_my_invoices(user)
    return UserServices(db).get_my_invoices(current_user)


@user_routes.get("/me/invoices/{id}")
async def get_my_invoice_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # If current_user is a dict, fetch the actual User object
    if (
        not isinstance(current_user, User)
        and isinstance(current_user, dict)
        and "id" in current_user
    ):
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserServices(db).get_my_invoice_by_id(id, user)
    return UserServices(db).get_my_invoice_by_id(id, current_user)


@user_routes.get("/me/courses/{course_id}/content")
async def get_course_contents(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # If current_user is a dict, fetch the actual User object
    if (
        not isinstance(current_user, User)
        and isinstance(current_user, dict)
        and "id" in current_user
    ):
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return CourseServices(db).get_course_with_content_by_id_for_user(
            course_id, user
        )
    return CourseServices(db).get_course_with_content_by_id_for_user(
        course_id, current_user
    )


@user_routes.get("/me/notifications")
async def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).get_my_notifications(current_user)


@user_routes.get("/me/notifications/{id}")
async def get_my_notification_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).get_my_notifications_by_id(id, current_user)


@user_routes.post("/me/notifications")
async def create_my_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).add_notification(current_user, notification)


@user_routes.put("/me/notifications/{id}")
async def update_my_notification(
    id: int,
    notification: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).update_notification(current_user, id, notification)


@user_routes.delete("/me/notifications/{id}")
async def delete_my_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).delete_notification(current_user, id)
