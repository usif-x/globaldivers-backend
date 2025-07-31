from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import *
from app.services.user import UserServices

user_routes = APIRouter(prefix="/users", tags=["User Endpoints"])


@user_routes.get("/me")
async def get_current_user(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user, from_attributes=True)


@user_routes.get("/{id}", response_model=UserResponse)
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
