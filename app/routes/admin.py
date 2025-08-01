from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_current_super_admin, get_db
from app.models.admin import Admin
from app.schemas import *
from app.schemas.admin import AdminResponse, AdminUpdate, AdminUpdatePassword
from app.schemas.user import UserResponse, UserUpdate
from app.services.admin import AdminServices

admin_routes = APIRouter(prefix="/admins", tags=["Admin Endpoints"])


@admin_routes.get(
    "/get-all-users",
    response_model=list[UserResponse],
    dependencies=[Depends(get_current_admin)],
)
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str = Query(None),
    email: str = Query(None),
    db: Session = Depends(get_db),
):
    return AdminServices(db).get_all_users(
        page=page, page_size=page_size, name=name, email=email
    )


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


@admin_routes.put("/edit-user/{id}", dependencies=[Depends(get_current_admin)])
async def edit_user_information(
    id: int, user: UserUpdate, db: Session = Depends(get_db)
):
    return AdminServices(db).edit_user_information(id, user)


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
