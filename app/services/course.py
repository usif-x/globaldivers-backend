from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.course import Course
from app.schemas.course import CourseResponse, CreateCourse, UpdateCourse


class CourseServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_course(self, course: CreateCourse):
        new_course = Course(**course.model_dump())
        self.db.add(new_course)
        self.db.commit()
        self.db.refresh(new_course)
        return new_course

    @db_exception_handler
    def get_all_courses(self):
        stmt = select(Course)
        courses = self.db.execute(stmt).scalars().all()
        return courses

    @db_exception_handler
    def get_course_by_id(self, id: int):
        stmt = select(Course).where(Course.id == id)
        course = self.db.execute(stmt).scalars().first()
        return course

    @db_exception_handler
    def update_course(self, id: int, course: UpdateCourse):
        stmt = select(Course).where(Course.id == id)
        course_db = self.db.execute(stmt).scalars().first()
        if not course_db:
            raise HTTPException(404, detail="Course not found")
        course_db.name = course.name
        course_db.description = course.description
        course_db.images = course.images
        course_db.is_image_list = course.is_image_list
        course_db.course_level = course.course_level
        course_db.course_duration = course.course_duration
        self.db.commit()
        self.db.refresh(course_db)
        return course_db

    @db_exception_handler
    def delete_course(self, id: int):
        stmt = select(Course).where(Course.id == id)
        course = self.db.execute(stmt).scalars().first()
        if course:
            self.db.delete(course)
            self.db.commit()
            return {"success": True, "message": "Course deleted successfully"}
        else:
            raise HTTPException(404, detail="Course not found")

    @db_exception_handler
    def delete_all_courses(self):
        self.db.query(Course).delete()
        self.db.commit()
        return {"success": True, "message": "All courses deleted successfully"}
