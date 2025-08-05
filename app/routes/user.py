from fastapi import APIRouter, Depends, Path
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import *
from app.services.course import CourseServices
from app.services.user import UserServices

user_routes = APIRouter(prefix="/users", tags=["User Endpoints"])


@user_routes.get("/me")
@cache(expire=600)
async def get_current_user(user: User = Depends(get_current_user)):
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
    return UserServices(db).update_user(user, current_user.id)


@user_routes.put("/update/password")
async def update_user_password(
    user: UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).update_user_password(user, current_user.id)


@user_routes.delete("/delete")
async def delete_user(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return UserServices(db).delete_my_account(current_user.id)


@user_routes.get("/me/testimonials")
async def get_my_testimonials(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return UserServices(db).get_my_testimonials(current_user.id)


@user_routes.get("/me/courses")
async def get_my_subscribed_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return UserServices(db).get_my_subscribed_courses(current_user.id)


@user_routes.get("/me/invoices")
async def get_my_invoices(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return UserServices(db).get_my_invoices(current_user)


@user_routes.get("/me/invoices/{id}")
async def get_my_invoice_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserServices(db).get_my_invoice_by_id(id, current_user)


@user_routes.get("/me/courses/{course_id}/content")
async def get_course_contents(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CourseServices(db).get_course_with_content_by_id_for_user(
        course_id, current_user
    )
