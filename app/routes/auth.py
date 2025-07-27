from app.services.auth import AuthServices
from fastapi import APIRouter, Depends
from app.schemas.auth import UserCreate, UserLogin, AdminCreate, AdminLogin
from app.core.dependencies import get_db
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_super_admin, get_current_user
from fastapi import status
from app.models.user import User




auth_routes = APIRouter(
  prefix="/auth",
  tags=["Auth Endpoints"]
)



@auth_routes.post("/register", status_code=status.HTTP_201_CREATED)
async def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
  return AuthServices(db).create_new_user(user)

@auth_routes.post("/login")
async def user_login(user: UserLogin, db: Session = Depends(get_db)):
  return AuthServices(db).user_login(user)

@auth_routes.get("/logout")
async def user_logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  return AuthServices(db).user_logout(user.id)


@auth_routes.post("/admin/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_super_admin)])
async def create_new_admin(admin: AdminCreate, db: Session = Depends(get_db)):
  return AuthServices(db).create_new_admin(admin)

@auth_routes.post("/admin/login")
async def admin_login(admin: AdminLogin, db: Session = Depends(get_db)):
  return AuthServices(db).admin_login(admin)


