from app.models.testimonial import Testimonial
from app.schemas.testimonial import CreateTestimonial, TestimonialResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException




class TestimonialServices:
  def __init__(self, db: Session):
    self.db = db




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
  


  def get_all_testimonials(self):
    stmt = select(Testimonial)
    testimonials = self.db.execute(stmt).scalars().all()
    return testimonials
  

  def get_accepted_testimonials(self):
    stmt = select(Testimonial).where(Testimonial.is_accepted == True)
    testimonials = self.db.execute(stmt).scalars().all()
    return testimonials
  
  def get_unaccepted_testimonials(self):
    stmt = select(Testimonial).where(Testimonial.is_accepted == False)
    testimonials = self.db.execute(stmt).scalars().all()
    return testimonials


  def get_testimonial_by_id(self, id: int):
    stmt = select(Testimonial).where(Testimonial.id == id)
    testimonial = self.db.execute(stmt).scalars().first()
    return testimonial
  

  def get_user_testimonials(self, user_id: int):
    stmt = select(Testimonial).where(Testimonial.testimonial_owner == user_id)
    testimonials = self.db.execute(stmt).scalars().all()
    return testimonials
  


  def delete_testimonial(self, id: int):
    stmt = select(Testimonial).where(Testimonial.id == id)
    testimonial = self.db.execute(stmt).scalars().first()
    if testimonial:
      self.db.delete(testimonial)
      self.db.commit()
      return {"success": True, "message": "Testimonial deleted successfully"}
    else:
      raise HTTPException(404, detail="Testimonial not found")
    

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
    


  def delete_all_testimonials(self):
    stmt = select(Testimonial)
    testimonials = self.db.execute(stmt).scalars().all()
    for testimonial in testimonials:
      self.db.delete(testimonial)
    self.db.commit()
    return {"success": True, "message": "All testimonials deleted successfully"}