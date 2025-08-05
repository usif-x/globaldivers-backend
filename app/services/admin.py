import math
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.core.hashing import hash_password, verify_password
from app.models.admin import Admin
from app.models.testimonial import Testimonial
from app.models.user import User
from app.schemas.admin import (
    AdminResponse,
    AdminUpdate,
    AdminUpdatePassword,
    PaginatedUsersResponse,
    PasswordUpdate,
)
from app.schemas.user import UserResponse, UserUpdate, UserUpdateStatus


class AdminServices:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self):
        stmt = select(User)
        users = self.db.execute(stmt).scalars().all()
        return users

    def get_all_users(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> PaginatedUsersResponse:
        offset = (page - 1) * page_size

        # Base query for filtering
        base_stmt = select(User)
        if name:
            if "@" in name:
                base_stmt = base_stmt.where(User.email.ilike(f"%{name}%"))
            else:
                base_stmt = base_stmt.where(User.full_name.ilike(f"%{name}%"))
        if email:
            base_stmt = base_stmt.where(User.email.ilike(f"%{email}%"))

        # Get total count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = self.db.execute(count_stmt).scalar()

        if total == 0:
            raise HTTPException(status_code=404, detail="No users found")

        # Get paginated users
        stmt = base_stmt.offset(offset).limit(page_size)
        users = self.db.execute(stmt).scalars().all()

        # Calculate pagination metadata
        total_pages = math.ceil(total / page_size)
        has_next = page < total_pages
        has_previous = page > 1
        next_page = page + 1 if has_next else None
        previous_page = page - 1 if has_previous else None

        return PaginatedUsersResponse(
            users=[
                UserResponse.model_validate(user, from_attributes=True)
                for user in users
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_page=next_page,
            previous_page=previous_page,
        )

    @db_exception_handler
    def get_all_admins(self) -> List[AdminResponse]:
        stmt = select(Admin)
        admins = self.db.execute(stmt).scalars().all()
        if not admins:
            raise HTTPException(404, detail="Admins not found")
        else:
            return [
                AdminResponse.model_validate(admin, from_attributes=True)
                for admin in admins
            ]

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
            return {
                "success": True,
                "message": "Admin Updated successfuly",
                "admin": AdminResponse.model_validate(
                    updated_admin, from_attributes=True
                ),
            }
        else:
            raise HTTPException(404, detail="Admin not found")

    @db_exception_handler
    def get_recent_users(self, limit: int = 10):
        if hasattr(User, "created_at"):
            stmt = select(User).order_by(desc(User.created_at)).limit(limit)
        else:
            stmt = select(User).order_by(desc(User.id)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    @db_exception_handler
    def update_admin_password(self, user: AdminUpdatePassword, id: int):
        stmt = select(Admin).where(Admin.id == id)
        updated_admin = self.db.execute(stmt).scalars().first()
        if verify_password(user.old_password, updated_admin.password):
            updated_admin.password = hash_password(user.new_password)
            self.db.commit()
            self.db.refresh(updated_admin)
            return {
                "success": True,
                "message": "Password Updated successfuly",
                "user": AdminResponse.model_validate(
                    updated_admin, from_attributes=True
                ),
            }
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
            return {
                "success": True,
                "message": "User Updated successfuly",
                "user": UserResponse.model_validate(updated_user, from_attributes=True),
            }
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
    def block_user(self, id: int):
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
    def edit_user_information(self, id: int, updated_user: UserUpdate):
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            user.full_name = updated_user.full_name
            user.email = updated_user.email
            self.db.commit()
            self.db.refresh(user)
            return {
                "success": True,
                "message": "User Updated successfuly",
                "user": UserResponse.model_validate(user, from_attributes=True),
            }
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def edit_user_password(self, id: int, new_password: PasswordUpdate):
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            user.password = hash_password(new_password.password)
            self.db.commit()
            self.db.refresh(user)
            return {
                "success": True,
                "message": "User Password Updated successfuly",
            }
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def get_user_testminals(self, id: int):
        stmt = select(User).where(User.id == id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.testimonials
        else:
            raise HTTPException(404, detail="User not found")

    @db_exception_handler
    def get_all_testimonials(self):
        stmt = select(Testimonial)
        testimonials = self.db.execute(stmt).scalars().all()
        return testimonials

    @db_exception_handler
    def get_accepted_testimonials(self):

        stmt = select(Testimonial).where(Testimonial.is_accepted == True)
        testimonials = self.db.execute(stmt).scalars().all()
        return testimonials

    @db_exception_handler
    def get_unaccepted_testimonials(self):
        stmt = select(Testimonial).where(Testimonial.is_accepted == False)
        testimonials = self.db.execute(stmt).scalars().all()
        return testimonials

    @db_exception_handler
    def get_testimonial_by_id(self, id: int):
        stmt = select(Testimonial).where(Testimonial.id == id)
        testimonial = self.db.execute(stmt).scalars().first()
        return testimonial

    @db_exception_handler
    def get_user_testimonials(self, user_id: int):
        stmt = select(Testimonial).where(Testimonial.testimonial_owner == user_id)
        testimonials = self.db.execute(stmt).scalars().all()
        return testimonials

    @db_exception_handler
    def delete_testimonial(self, id: int):
        stmt = select(Testimonial).where(Testimonial.id == id)
        testimonial = self.db.execute(stmt).scalars().first()
        if testimonial:
            self.db.delete(testimonial)
            self.db.commit()
            return {"success": True, "message": "Testimonial deleted successfully"}
        else:
            raise HTTPException(404, detail="Testimonial not found")

    @db_exception_handler
    def accept_testimonial(self, id: int):
        stmt = select(Testimonial).where(Testimonial.id == id)
        testimonial = self.db.execute(stmt).scalars().first()
        if testimonial:
            testimonial.is_accepted = True
            testimonial.is_rejected = False
            self.db.commit()
            self.db.refresh(testimonial)
            return {"success": True, "message": "Testimonial accepted successfully"}
        else:
            raise HTTPException(404, detail="Testimonial not found")

    @db_exception_handler
    def reject_testimonial(self, id: int):
        stmt = select(Testimonial).where(Testimonial.id == id)
        testimonial = self.db.execute(stmt).scalars().first()
        if testimonial:
            testimonial.is_accepted = False
            testimonial.is_rejected = True
            self.db.commit()
            self.db.refresh(testimonial)
            return {"success": True, "message": "Testimonial rejected successfully"}
        else:
            raise HTTPException(404, detail="Testimonial not found")

    @db_exception_handler
    def unaccept_testimonial(self, id: int):
        stmt = select(Testimonial).where(Testimonial.id == id)
        testimonial = self.db.execute(stmt).scalars().first()
        if testimonial:
            testimonial.is_accepted = False
            self.db.commit()
            self.db.refresh(testimonial)
            return {"success": True, "message": "Testimonial unaccepted successfully"}
        else:
            raise HTTPException(404, detail="Testimonial not found")

    @db_exception_handler
    def delete_all_testimonials(self):
        stmt = select(Testimonial)
        testimonials = self.db.execute(stmt).scalars().all()
        for testimonial in testimonials:
            self.db.delete(testimonial)
        self.db.commit()
        return {"success": True, "message": "All testimonials deleted successfully"}
