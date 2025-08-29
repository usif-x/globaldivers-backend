from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_current_super_admin, get_db
from app.models.admin import Admin
from app.schemas import *
from app.schemas.admin import (
    AdminEnrollmentRequest,
    AdminResponse,
    AdminUpdate,
    AdminUpdatePassword,
    PaginatedUsersResponse,
    PasswordUpdate,
)
from app.schemas.user import UserResponse, UserUpdate
from app.services.admin import AdminServices
from app.services.course import CourseServices

admin_routes = APIRouter(prefix="/admins", tags=["Admin Endpoints"])


@admin_routes.get(
    "/get-all-users",
    response_model=PaginatedUsersResponse,
    summary="Get all users with pagination",
    description="Retrieve a paginated list of users with optional filtering by name and email",
)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of users per page"),
    name: str = Query(
        None, description="Filter by user full name (case-insensitive partial match)"
    ),
    email: str = Query(
        None, description="Filter by email (case-insensitive partial match)"
    ),
    db: Session = Depends(get_db),
):
    return AdminServices(db).get_all_users(
        page=page, page_size=page_size, name=name, email=email
    )


@admin_routes.get(
    "/get-users",
)
async def get_all_users(
    db: Session = Depends(get_db),
):
    return AdminServices(db).get_users()


@admin_routes.get("/get-recent-users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
):
    users = AdminServices(db).get_recent_users(limit=8)
    return users


@admin_routes.get(
    "/get-all-admins",
    response_model=list[AdminResponse],
    dependencies=[Depends(get_current_super_admin)],
)
async def get_all_admins(db: Session = Depends(get_db)):
    return AdminServices(db).get_all_admins()


@admin_routes.put("/update")
async def update_admin(
    admin: AdminUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return AdminServices(db).update_admin(admin, current_admin.id)


@admin_routes.put("/update-admin/{id}", dependencies=[Depends(get_current_super_admin)])
async def update_admin_password(
    id: int, admin: AdminUpdate, db: Session = Depends(get_db)
):
    return AdminServices(db).update_admin(admin, id)


@admin_routes.put("/update/password")
async def update_admin_password(
    admin: AdminUpdatePassword,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return AdminServices(db).update_admin_password(admin, current_admin.id)


@admin_routes.put(
    "/update-admin/{id}/password", dependencies=[Depends(get_current_super_admin)]
)
async def update_admin_password(
    id: int, admin: AdminUpdatePassword, db: Session = Depends(get_db)
):
    return AdminServices(db).update_admin_password(admin, id)


@admin_routes.delete(
    "/delete-admin/{id}", dependencies=[Depends(get_current_super_admin)]
)
async def delete_admin(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).delete_admin(id)


@admin_routes.delete("/delete-user/{id}", dependencies=[Depends(get_current_admin)])
async def delete_user(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).delete_user(id)


@admin_routes.get("/block-user/{id}", dependencies=[Depends(get_current_admin)])
async def block_user(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).block_user(id)


@admin_routes.get("/unblock-user/{id}", dependencies=[Depends(get_current_admin)])
async def unblock_user(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).unblock_user(id)


@admin_routes.put("/update-user/{id}", dependencies=[Depends(get_current_admin)])
async def edit_user_information(
    id: int, user: UserUpdate, db: Session = Depends(get_db)
):
    return AdminServices(db).edit_user_information(id, user)


@admin_routes.put(
    "/update-user-password/{id}", dependencies=[Depends(get_current_admin)]
)
async def edit_user_password(
    id: int, password: PasswordUpdate, db: Session = Depends(get_db)
):
    return AdminServices(db).edit_user_password(id, password)


@admin_routes.get(
    "/get-user-testminals/{id}", dependencies=[Depends(get_current_admin)]
)
async def get_user_testminals(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).get_user_testminals(id)


@admin_routes.put("/accept-testimonial/{id}", dependencies=[Depends(get_current_admin)])
async def accept_testimonial(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).accept_testimonial(id)


@admin_routes.put("/reject-testimonial/{id}", dependencies=[Depends(get_current_admin)])
async def reject_testimonial(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).reject_testimonial(id)


@admin_routes.get("/get-all-testimonials", dependencies=[Depends(get_current_admin)])
async def get_all_testimonials(db: Session = Depends(get_db)):
    return AdminServices(db).get_all_testimonials()


@admin_routes.delete(
    "/delete-all-testimonials", dependencies=[Depends(get_current_admin)]
)
async def delete_all_testimonials(db: Session = Depends(get_db)):
    return AdminServices(db).delete_all_testimonials()


@admin_routes.get(
    "/get-accepted-testimonials", dependencies=[Depends(get_current_admin)]
)
async def get_accepted_testimonials(db: Session = Depends(get_db)):
    return AdminServices(db).get_accepted_testimonials()


@admin_routes.get(
    "/get-unaccepted-testimonials", dependencies=[Depends(get_current_admin)]
)
async def get_unaccepted_testimonials(db: Session = Depends(get_db)):
    return AdminServices(db).get_unaccepted_testimonials()


@admin_routes.delete(
    "/delete-testimonial/{id}", dependencies=[Depends(get_current_admin)]
)
async def delete_testimonial(id: int, db: Session = Depends(get_db)):
    return AdminServices(db).delete_testimonial(id)


@admin_routes.post("/enroll-user", dependencies=[Depends(get_current_admin)])
async def enroll_user_to_course_by_admin(
    enrollment_data: AdminEnrollmentRequest, db: Session = Depends(get_db)
):
    return CourseServices(db).enroll_user_in_course(
        user_id=enrollment_data.user_id, course_id=enrollment_data.course_id
    )
