from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_super_admin, get_current_user, get_db
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.auth import AdminCreate, AdminLogin, UserCreate, UserLogin
from app.services.auth import AuthServices

auth_routes = APIRouter(
    prefix="/auth",
    tags=["Auth Endpoints"],
)


@auth_routes.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_new_user(
    request: Request, user: UserCreate, db: Session = Depends(get_db)
):
    return AuthServices(db).create_new_user(user)


@auth_routes.post("/login")
@limiter.limit("3/minute")
async def user_login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    return AuthServices(db).user_login(user)


@auth_routes.get("/logout")
async def user_logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AuthServices(db).user_logout(user.id)


@auth_routes.post(
    "/admin/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_super_admin)],
)
@limiter.limit("3/minute")
async def create_new_admin(
    request: Request, admin: AdminCreate, db: Session = Depends(get_db)
):
    return AuthServices(db).create_new_admin(admin)


@auth_routes.post("/admin/login")
@limiter.limit("3/minute")
async def admin_login(
    request: Request, admin: AdminLogin, db: Session = Depends(get_db)
):
    return AuthServices(db).admin_login(admin)


@auth_routes.get("/verify")
async def verify_token(request: Request, token: str, db: Session = Depends(get_db)):
    return AuthServices(db).verify_token(token)
