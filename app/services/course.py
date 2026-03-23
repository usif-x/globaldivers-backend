from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.exception_handler import db_exception_handler
from app.core.telegram import notify_admins
from app.models.course import Course
from app.models.course_content import CourseContent
from app.models.user import User
from app.schemas.course import CourseResponse, CreateCourse, UpdateCourse
from app.utils.storage import delete_file, get_public_url
from app.utils.upload_img import upload_images


class CourseServices:
    def __init__(self, db: Session):
        self.db = db

    def _convert_keys_to_urls(self, keys: List[str]) -> List[str]:
        """Convert S3 object keys to full public URLs."""
        if not keys:
            return []
        return [get_public_url(key) for key in keys]

    @db_exception_handler
    async def create_course(
        self, course: CreateCourse, images: List[UploadFile] = None
    ):
        image_keys = []
        if images:
            try:
                image_keys = await upload_images(images)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload images: {str(e)}"
                )

        course_data = course.model_dump(exclude={"contents"})
        course_data["images"] = image_keys

        new_course = Course(**course_data)
        self.db.add(new_course)
        self.db.commit()
        self.db.refresh(new_course)

        # Add contents if provided
        if course.contents:
            for content in course.contents:
                new_content = CourseContent(
                    course_id=new_course.id, **content.model_dump()
                )
                self.db.add(new_content)
            self.db.commit()

        new_course.images = self._convert_keys_to_urls(new_course.images)
        return new_course

    @db_exception_handler
    def get_all_courses(self):
        stmt = select(Course)
        courses = self.db.execute(stmt).scalars().all()

        for course in courses:
            course.images = self._convert_keys_to_urls(course.images)

        return courses

    @db_exception_handler
    def get_all_courses_with_contents(self):
        stmt = select(Course).options(joinedload(Course.contents))
        courses = self.db.execute(stmt).unique().scalars().all()

        for course in courses:
            course.images = self._convert_keys_to_urls(course.images)

        return courses

    @db_exception_handler
    def get_course_by_id(self, id: int):
        stmt = select(Course).where(Course.id == id)
        course = self.db.execute(stmt).scalars().first()
        if course:
            course.images = self._convert_keys_to_urls(course.images)
        return course

    @db_exception_handler
    def get_course_with_contents_by_id(self, id: int):
        stmt = (
            select(Course).where(Course.id == id).options(joinedload(Course.contents))
        )
        course = self.db.execute(stmt).scalars().first()
        if not course:
            raise HTTPException(404, detail="Course not found")

        course.images = self._convert_keys_to_urls(course.images)
        return course

    @db_exception_handler
    def get_course_with_content_by_id_for_user(self, id: int, user: User):
        user_stmt = select(User).where(User.id == user.id)
        user_db = self.db.execute(user_stmt).scalars().first()
        if not user_db:
            raise HTTPException(404, detail="User not found")

        course_stmt = (
            select(Course)
            .join(Course.subscribers)
            .where(
                and_(
                    Course.id == id,
                    User.id == user.id,
                )
            )
            .options(joinedload(Course.contents))
        )
        course = self.db.execute(course_stmt).scalars().first()
        if not course:
            raise HTTPException(
                403, detail="You not subscribed to this course or course not found"
            )

        course.images = self._convert_keys_to_urls(course.images)
        return course

    @db_exception_handler
    async def update_course(
        self, id: int, course_update: UpdateCourse, images: List[UploadFile] = None
    ):
        course_db = self.db.query(Course).filter(Course.id == id).first()
        if not course_db:
            raise HTTPException(status_code=404, detail="Course not found")

        update_data = course_update.model_dump(exclude_unset=True)
        new_contents_data = update_data.pop("contents", None)

        if images:
            try:
                # Delete old images from S3
                if course_db.images:
                    for old_key in course_db.images:
                        try:
                            delete_file(old_key)
                        except Exception as e:
                            print(f"Failed to delete old image {old_key}: {e}")

                new_image_keys = await upload_images(images)
                update_data["images"] = new_image_keys

            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload new images: {str(e)}"
                )

        for key, value in update_data.items():
            setattr(course_db, key, value)

        if new_contents_data is not None:
            self.db.query(CourseContent).filter(CourseContent.course_id == id).delete()
            for content_item_data in new_contents_data:
                new_content = CourseContent(**content_item_data, course_id=course_db.id)
                self.db.add(new_content)

        self.db.commit()
        self.db.refresh(course_db)

        course_db.images = self._convert_keys_to_urls(course_db.images)
        return course_db

    @db_exception_handler
    def delete_course(self, id: int):
        try:
            stmt = select(Course).where(Course.id == id)
            course = self.db.execute(stmt).scalars().first()
            if course:
                if course.images:
                    for key in course.images:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete image {key}: {e}")

                self.db.delete(course)
                self.db.commit()
                return {"success": True, "message": "Course deleted successfully"}
            else:
                raise HTTPException(404, detail="Course not found")
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting course: {str(e)}"}

    @db_exception_handler
    def delete_all_courses(self):
        try:
            courses = self.db.execute(select(Course)).scalars().all()

            for course in courses:
                if course.images:
                    for key in course.images:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete image {key}: {e}")

            self.db.query(Course).delete()
            self.db.commit()
            return {"success": True, "message": "All courses deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting courses: {str(e)}"}

    @db_exception_handler
    def add_contents_to_course(self, course_id: int, contents: list):
        course = self.get_course_by_id(course_id)
        if not course:
            raise HTTPException(404, detail="Course not found")

        for content in contents:
            new_content = CourseContent(course_id=course_id, **content.model_dump())
            self.db.add(new_content)
        self.db.commit()
        return {"success": True, "message": "Contents added successfully"}

    @db_exception_handler
    def enroll_user_in_course(self, user_id: int, course_id: int):
        """Subscribes a user to a specific course."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if course in user.subscribed_courses:
            raise HTTPException(
                status_code=400,
                detail="User is already enrolled in this course",
            )

        user.subscribed_courses.append(course)
        self.db.commit()

        return {"message": f"Successfully enrolled in {course.name}"}

    @db_exception_handler
    def send_course_inquiry(self, inquiry_data: dict):
        """Sends a course inquiry notification to admins via Telegram."""
        course_id = inquiry_data.get("course_id")
        course_name = inquiry_data.get("course_name")
        full_name = inquiry_data.get("full_name")
        email = inquiry_data.get("email")
        phone = inquiry_data.get("phone")
        message = inquiry_data.get("message", "No message provided")
        number_of_people = inquiry_data.get("number_of_people", 1)
        status = inquiry_data.get("status", "pending")

        telegram_message = (
            "<b>New Course Inquiry</b>\n"
            "---\n\n"
            f"<b>Course:</b> {course_name}\n"
            f"<b>Course ID:</b> <code>{course_id}</code>\n\n"
            "---\n\n"
            f"<b>Name:</b> {full_name}\n"
            f"<b>Email:</b> {email}\n"
            f"<b>Phone:</b> {phone}\n"
            f"<b>Number of People:</b> {number_of_people}\n\n"
            "---\n\n"
            f"<b>Message:</b>\n{message}\n\n"
            "---\n\n"
            f"<b>Status:</b> <b>{status.upper()}</b>"
        )

        try:
            notify_admins(telegram_message)
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")

        return {
            "success": True,
            "message": "Course inquiry received successfully. Our team will contact you soon!",
        }
