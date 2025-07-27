from app.models.testimonial import Testimonial
from app.schemas.testimonial import CreateTestimonial, TestimonialResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.exception_handler import db_exception_handler



class TestimonialServices:
  def __init__(self, db: Session):
    self.db = db



  @db_exception_handler
  def create_testimonial(self, testimonial: CreateTestimonial, testimonial_owner: int):
    new_testimonial = Testimonial(
      testimonial_owner=testimonial_owner,
      description=testimonial.description,
      rating=testimonial.rating,
    )
    self.db.add(new_testimonial)
    self.db.commit()
    self.db.refresh(new_testimonial)
    return new_testimonial
  

  @db_exception_handler
  def get_all_testimonials(self):
    stmt = select(Testimonial)
    testimonials = self.db.execute(stmt).scalars().all()
    return testimonials
  
  @db_exception_handler
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
      self.db.commit()
      self.db.refresh(testimonial)
      return {"success": True, "message": "Testimonial accepted successfully"}
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