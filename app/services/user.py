from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserUpdatePassword
from sqlalchemy import select
from fastapi import HTTPException
from app.core.hashing import verify_password, hash_password
from app.core.exception_handler import db_exception_handler
from datetime import datetime, timezone



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
      return {"success": True, 
              "message": "User Updated successfuly", 
              "user": UserResponse.model_validate(updated_user,from_attributes=True)}
    else:
      raise HTTPException(404, detail="user not found")
    
  @db_exception_handler
  def update_user_password(self, user: UserUpdatePassword, id:int):
    stmt = select(User).where(User.id == id)
    updated_user = self.db.execute(stmt).scalars().first()
    if verify_password(user.old_password, updated_user.password):
      updated_user.password = hash_password(user.new_password)
      updated_user.last_login = datetime.now(timezone.utc)
      self.db.commit()
      self.db.refresh(updated_user)
      return {"success": True, 
              "message": "Password Updated successfuly", 
              "user": UserResponse.model_validate(updated_user,from_attributes=True)}
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