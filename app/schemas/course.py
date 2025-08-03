from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# --- Course Content Schemas ---
class CourseContentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: str  # e.g., "video", "pdf"
    content_url: Optional[str] = None
    order: int = 0


class CourseContentResponse(CourseContentCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Course Schemas ---
class CreateCourse(BaseModel):
    name: str
    description: str
    price: int
    images: List[str]
    is_image_list: bool
    course_level: str
    course_duration: int
    course_type: str
    has_certificate: bool
    certificate_type: str
    has_online_content: bool
    contents: Optional[List[CourseContentCreate]] = None


class UpdateCourse(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    images: Optional[List[str]] = None
    is_image_list: Optional[bool] = None
    course_level: Optional[str] = None
    course_duration: Optional[int] = None
    course_type: Optional[str] = None
    has_certificate: Optional[bool] = None
    certificate_type: Optional[str] = None
    has_online_content: Optional[bool] = None
    contents: Optional[List[CourseContentCreate]] = None


class EnrollCourse(BaseModel):
    course_id: int
    user_id: int


class CourseResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    images: List[str]
    is_image_list: bool
    course_level: str
    course_duration: int
    course_type: str
    has_certificate: bool
    certificate_type: str
    has_online_content: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Subscribed Course Response ---
class SubscribedCourseResponse(CourseResponse):
    contents: List[CourseContentResponse] = []

    class Config:
        from_attributes = True
