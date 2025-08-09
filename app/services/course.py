from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exception_handler import db_exception_handler
from app.models.course import Course
from app.models.course_content import CourseContent
from app.models.user import User
from app.schemas.course import CourseResponse, CreateCourse, UpdateCourse


class CourseServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_course(self, course: CreateCourse):
        new_course = Course(**course.model_dump(exclude={"contents"}))
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

        return new_course

    @db_exception_handler
    def get_all_courses(self):
        stmt = select(Course)
        courses = self.db.execute(stmt).scalars().all()
        return courses

    @db_exception_handler
    def get_all_courses_with_contents(self):
        stmt = select(Course).options(joinedload(Course.contents))
        courses = self.db.execute(stmt).unique().scalars().all()
        return courses

    @db_exception_handler
    def get_course_by_id(self, id: int):
        stmt = select(Course).where(Course.id == id)
        course = self.db.execute(stmt).scalars().first()
        return course

    @db_exception_handler
    def get_course_with_contents_by_id(self, id: int):
        stmt = (
            select(Course).where(Course.id == id).options(joinedload(Course.contents))
        )
        course = self.db.execute(stmt).scalars().first()
        if not course:
            raise HTTPException(404, detail="Course not found")
        return course

    @db_exception_handler
    def get_course_with_content_by_id_for_user(self, id: int, user: User):
        # أولاً نتأكد إن اليوزر موجود
        user_stmt = select(User).where(User.id == user.id)
        user_db = self.db.execute(user_stmt).scalars().first()
        if not user_db:
            raise HTTPException(404, detail="User not found")

        # نجلب الكورس مع المحتوى ولكن فقط إذا اليوزر مشترك فيه
        course_stmt = (
            select(Course)
            .join(Course.subscribers)  # يربط عن طريق العلاقة subscribers
            .where(
                and_(
                    Course.id == id,
                    User.id == user.id,  # شرط إن اليوزر موجود ضمن المشتركين
                )
            )
            .options(joinedload(Course.contents))
        )
        course = self.db.execute(course_stmt).scalars().first()
        if not course:
            # يا إما الكورس مش موجود، يا إما اليوزر مش مشترك فيه
            raise HTTPException(
                403, detail="You not subscribed to this course or course not found"
            )

        return course

    @db_exception_handler
    def update_course(self, id: int, course_update: UpdateCourse):
        # 1. Fetch the course from the database
        course_db = self.db.query(Course).filter(Course.id == id).first()
        if not course_db:
            raise HTTPException(status_code=404, detail="Course not found")

        # 2. Get the update data and separate the 'contents'
        update_data = course_update.model_dump(exclude_unset=True)
        new_contents_data = update_data.pop("contents", None)

        # 3. Update the simple, flat attributes of the course
        for key, value in update_data.items():
            setattr(course_db, key, value)

        # 4. Handle the nested 'contents' update if they were provided
        if new_contents_data is not None:
            # First, delete all existing contents for this course to ensure a clean update
            self.db.query(CourseContent).filter(CourseContent.course_id == id).delete()

            # Second, create new CourseContent objects from the provided data
            for content_item_data in new_contents_data:
                new_content = CourseContent(**content_item_data, course_id=course_db.id)
                self.db.add(new_content)

        # 5. Commit the transaction and refresh the course object
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
        """
        Subscribes a user to a specific course.
        """
        # 1. Fetch the user and the course
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # 2. Check if the user is already subscribed to prevent duplicates
        if course in user.subscribed_courses:
            raise HTTPException(
                status_code=400,  # Bad Request
                detail="User is already enrolled in this course",
            )

        # 3. Perform the enrollment by appending to the relationship
        user.subscribed_courses.append(course)

        # 4. Commit the change to the database
        self.db.commit()

        return {"message": f"Successfully enrolled in {course.name}"}
