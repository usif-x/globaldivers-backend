from sqlalchemy.orm import Session
from app.schemas.admin import AdminResponse, AdminUpdate, AdminUpdatePassword
from app.schemas.user import UserResponse, UserUpdateStatus, UserUpdate
from sqlalchemy import select
from typing import List, Optional
from fastapi import HTTPException
from app.models.admin import Admin
from app.models.user import User
from app.core.hashing import verify_password, hash_password
from app.core.exception_handler import db_exception_handler



class AdminServices:
  def __init__(self, db: Session):
    self.db = db

  def get_all_users(
    self,
    page: int = 1,
    page_size: int = 20,
    name: Optional[str] = None,
    email: Optional[str] = None
) -> List[UserResponse]:
    offset = (page - 1) * page_size
    stmt = select(User)
    if name:
        stmt = stmt.where(User.full_name.ilike(f"%{name}%"))
    if email:
        stmt = stmt.where(User.email.ilike(f"%{email}%"))
    stmt = stmt.offset(offset).limit(page_size)
    users = self.db.execute(stmt).scalars().all()
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    
    return [UserResponse.model_validate(user, from_attributes=True) for user in users]
  

  @db_exception_handler
  def get_all_admins(self) -> List[AdminResponse]:
    stmt = select(Admin)
    admins = self.db.execute(stmt).scalars().all()
    if not admins:
      raise HTTPException(404, detail="Admins not found")
    else:
      return [AdminResponse.model_validate(admin, from_attributes=True) for admin in admins]

  @db_exception_handler
  def update_admin(self, admin: AdminUpdate, id: int):
    stmt = select(Admin).where(Admin.id == id)
    updated_admin = self.db.execute(stmt).scalars().first()
    if updated_admin:
      data = admin.model_dump(exclude_unset=True)
      for field, value in data.items():
        setattr(updated_admin, field, value)
      self.db.commit()
      self.db.refresh(updated_admin)
      return {"success": True, 
              "message": "Admin Updated successfuly", 
              "admin": AdminResponse.model_validate(updated_admin,from_attributes=True)}
    else:
      raise HTTPException(404, detail="Admin not found")
    

    
  @db_exception_handler
  def update_admin_password(self, user: AdminUpdatePassword, id:int):
    stmt = select(Admin).where(Admin.id == id)
    updated_admin = self.db.execute(stmt).scalars().first()
    if verify_password(user.old_password, updated_admin.password):
      updated_admin.password = hash_password(user.new_password)
      self.db.commit()
      self.db.refresh(updated_admin)
      return {"success": True, 
              "message": "Password Updated successfuly", 
              "user": AdminResponse.model_validate(updated_admin,from_attributes=True)}
    else:
      raise HTTPException(400, detail="Invalid cerdentials")
    
  @db_exception_handler
  def update_user_status(self, status: UserUpdateStatus, id: int):
    stmt = select(User).where(User.id == id)
    updated_user = self.db.execute(stmt).scalars().first()
    if updated_user:
      data = status.model_dump(exclude_unset=True)
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
  def delete_user(self, id: int):
    stmt = select(User).where(User.id == id)
    user = self.db.execute(stmt).scalars().first()
    if user:
      self.db.delete(user)
      self.db.commit()
      return {"success": True, "message": "User deleted successfully"}
    else:
      raise HTTPException(404, detail="User not found")

  @db_exception_handler
  def delete_admin(self, id: int):
    stmt = select(Admin).where(Admin.id == id)
    admin = self.db.execute(stmt).scalars().first()
    if admin:
      self.db.delete(admin)
      self.db.commit()
      return {"success": True, "message": "Admin deleted successfully"}
    else:
      raise HTTPException(404, detail="Admin not found")
    

  @db_exception_handler
  def block_user(self,id: int):
    stmt = select(User).where(User.id == id)
    user = self.db.execute(stmt).scalars().first()
    if user:
      user.is_active = False
      user.is_blocked = True
      self.db.commit()
      return {"success": True, "message": "User blocked successfully"}
    else:
      raise HTTPException(404, detail="User not found")
    
  @db_exception_handler
  def unblock_user(self, id: int):
    stmt = select(User).where(User.id == id)
    user = self.db.execute(stmt).scalars().first()
    if user:
      user.is_active = True
      user.is_blocked = False
      self.db.commit()
      return {"success": True, "message": "User unblocked successfully"}
    else:
      raise HTTPException(404, detail="User not found")
    
  @db_exception_handler
  def edit_user_information(self, id: int, user: UserUpdate):
    stmt = select(User).where(User.id == id)
    user = self.db.execute(stmt).scalars().first()
    if user:
      data = user.model_dump(exclude_unset=True)
      for field, value in data.items():
        setattr(user, field, value)
      self.db.commit()
      self.db.refresh(user)
      return {"success": True, 
              "message": "User Updated successfuly", 
              "user": UserResponse.model_validate(user,from_attributes=True)}
    else:
      raise HTTPException(404, detail="User not found")