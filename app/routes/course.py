from fastapi import APIRouter, Depends, Path
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.course import (
    CourseInquiry,
    CourseResponse,
    CreateCourse,
    EnrollCourse,
    SubscribedCourseResponse,
    UpdateCourse,
)
from app.services.course import CourseServices

course_routes = APIRouter(prefix="/courses", tags=["Course Endpoints"])


@course_routes.get("/", response_model=list[CourseResponse])
@cache(expire=600)
async def get_all_courses(db: Session = Depends(get_db)):
    return CourseServices(db).get_all_courses()


@course_routes.get(
    "/content",
    response_model=list[SubscribedCourseResponse],
)
async def get_all_courses_with_contents(db: Session = Depends(get_db)):
    return CourseServices(db).get_all_courses_with_contents()


@course_routes.get("/{id}", response_model=CourseResponse)
async def get_course_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return CourseServices(db).get_course_by_id(id)


@course_routes.get(
    "/{id}/content",
    response_model=SubscribedCourseResponse,
)
async def get_course_content_by_id(
    id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    return CourseServices(db).get_course_with_contents_by_id(id)


@course_routes.post(
    "/", response_model=CourseResponse, dependencies=[Depends(get_current_admin)]
)
async def create_course(course: CreateCourse, db: Session = Depends(get_db)):
    return CourseServices(db).create_course(course)


@course_routes.put(
    "/{id}", response_model=CourseResponse, dependencies=[Depends(get_current_admin)]
)
async def update_course(course: UpdateCourse, id: int, db: Session = Depends(get_db)):
    return CourseServices(db).update_course(id, course)


@course_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_course(id: int, db: Session = Depends(get_db)):
    return CourseServices(db).delete_course(id)


@course_routes.delete("/delete-all", dependencies=[Depends(get_current_admin)])
async def delete_all_courses(db: Session = Depends(get_db)):
    return CourseServices(db).delete_all_courses()


@course_routes.put("/{course_id}/content", dependencies=[Depends(get_current_admin)])
async def add_contents_to_course(
    course_id: int, contents: list, db: Session = Depends(get_db)
):
    return CourseServices(db).add_contents_to_course(course_id, contents)


@course_routes.post("/enroll")
async def enroll_in_course(
    data: EnrollCourse,
    db: Session = Depends(get_db),
):
    """
    Enrolls the current authenticated user in a course.
    """
    return CourseServices(db).enroll_user_in_course(
        user_id=data.user_id, course_id=data.course_id
    )


@course_routes.post("/{course_id}/inquire")
async def send_course_inquiry(
    course_id: int,
    inquiry: CourseInquiry,
    db: Session = Depends(get_db),
):
    """
    Sends a course inquiry to admins via Telegram.
    No authentication required for public course inquiries.
    """
    return CourseServices(db).send_course_inquiry(inquiry.model_dump())
