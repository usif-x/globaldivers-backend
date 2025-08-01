from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.testimonial import CreateTestimonial, TestimonialResponse
from app.services.testimonial import TestimonialServices

testimonial_routes = APIRouter(prefix="/testimonials", tags=["Testimonial Endpoints"])


@testimonial_routes.post("/create")
async def create_testimonial(
    testimonial: CreateTestimonial,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return TestimonialServices(db).create_testimonial(testimonial, user)


@testimonial_routes.get("/all-with-users")
async def get_all_testimonials(db: Session = Depends(get_db)):
    return TestimonialServices(db).get_all_with_users()


@testimonial_routes.get("/{id}")
async def get_testimonial_by_id(
    id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    return TestimonialServices(db).get_testimonial_by_id(id)


@testimonial_routes.put("/{id}", dependencies=[Depends(get_current_admin)])
async def accept_testimonial(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return TestimonialServices(db).accept_testimonial(id)


@testimonial_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_testimonial(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return TestimonialServices(db).delete_testimonial(id)
