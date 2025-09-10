from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, joinedload

from app.core.exception_handler import db_exception_handler
from app.models.testimonial import Testimonial
from app.models.user import User
from app.schemas.testimonial import CreateTestimonial
from sqlalchemy.exc import SQLAlchemyError



class TestimonialServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_testimonial(self, testimonial: CreateTestimonial, user: User):
        new_testimonial = Testimonial(
            user=user,
            description=testimonial.description,
            rating=testimonial.rating,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(new_testimonial)
        self.db.commit()
        self.db.refresh(new_testimonial)
        return {"success": True, "message": "Testimonial created successfully"}

    @db_exception_handler
    def get_all_testimonials(self):
        stmt = select(Testimonial).where(Testimonial.is_accepted == True)
        testimonials = self.db.execute(stmt).scalars().all()
        return testimonials

    @db_exception_handler
    def get_all_with_users(self):
        stmt = (
            select(Testimonial)
            .options(joinedload(Testimonial.user))
            .where(Testimonial.is_accepted == True)
        )
        testimonials = self.db.execute(stmt).scalars().all()

        result = []
        for testimonial in testimonials:
            result.append(
                {
                    "id": testimonial.id,
                    "description": testimonial.description,
                    "rating": testimonial.rating,
                    "created_at": testimonial.created_at,
                    "user": {
                        "full_name": testimonial.user.full_name,
                    },
                }
            )
        return result

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
        stmt = select(User).where(User.id == user_id)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.testimonials
        else:
            raise HTTPException(404, detail="User not found")

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
    def delete_all_testimonials(self):
        try:
            self.db.execute(delete(Testimonial))
            self.db.commit()
            return {"success": True, "message": "All testimonials deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting testimonials: {str(e)}"}


