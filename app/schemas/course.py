from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CreateCourse(BaseModel):
  name: str
  description: str
  price: int
  images: List[str]
  is_image_list: bool
  course_level: str
  course_duration: int

class CourseResponse(BaseModel):
  id: int
  name: str
  description: str
  price: int
  images: List[str]
  is_image_list: bool
  course_level: str
  course_duration: int
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True

class UpdateCourse(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  price: Optional[int] = None
  images: Optional[List[str]] = None
  is_image_list: Optional[bool] = None
  course_level: Optional[str] = None
  course_duration: Optional[int] = None



