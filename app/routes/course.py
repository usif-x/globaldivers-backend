from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Path, UploadFile
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.course import (
    CourseContentCreate,
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
async def create_course(
    name: str = Form(...),
    description: str = Form(...),
    price_available: bool = Form(...),
    price: int = Form(...),
    is_image_list: bool = Form(False),
    course_level: str = Form(...),
    course_duration: int = Form(...),
    course_duration_unit: str = Form(...),
    provider: str = Form(...),
    has_discount: bool = Form(False),
    discount_requires_min_people: bool = Form(False),
    discount_always_available: bool = Form(False),
    discount_percentage: int = Form(0),
    discount_min_people: int = Form(0),
    course_type: str = Form(...),
    has_certificate: bool = Form(...),
    certificate_type: str = Form(...),
    has_online_content: bool = Form(False),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Create course object from form data
    course_data = CreateCourse(
        name=name,
        description=description,
        price_available=price_available,
        price=price,
        images=[],  # Will be filled by the service
        is_image_list=is_image_list,
        course_level=course_level,
        course_duration=course_duration,
        course_duration_unit=course_duration_unit,
        provider=provider,
        has_discount=has_discount,
        discount_requires_min_people=discount_requires_min_people,
        discount_always_available=discount_always_available,
        discount_percentage=discount_percentage,
        discount_min_people=discount_min_people,
        course_type=course_type,
        has_certificate=has_certificate,
        certificate_type=certificate_type,
        has_online_content=has_online_content,
        contents=None,  # Course contents can be added separately
    )

    return await CourseServices(db).create_course(course_data, images)


@course_routes.put(
    "/{id}", response_model=CourseResponse, dependencies=[Depends(get_current_admin)]
)
async def update_course(
    id: int,
    name: str = Form(None),
    description: str = Form(None),
    price_available: bool = Form(None),
    price: int = Form(None),
    is_image_list: bool = Form(None),
    course_level: str = Form(None),
    course_duration: int = Form(None),
    course_duration_unit: str = Form(None),
    provider: str = Form(None),
    has_discount: bool = Form(None),
    discount_requires_min_people: bool = Form(None),
    discount_always_available: bool = Form(None),
    discount_percentage: int = Form(None),
    discount_min_people: int = Form(None),
    course_type: str = Form(None),
    has_certificate: bool = Form(None),
    certificate_type: str = Form(None),
    has_online_content: bool = Form(None),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Create update object from form data, excluding None values
    update_data = {}

    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if price_available is not None:
        update_data["price_available"] = price_available
    if price is not None:
        update_data["price"] = price
    if is_image_list is not None:
        update_data["is_image_list"] = is_image_list
    if course_level is not None:
        update_data["course_level"] = course_level
    if course_duration is not None:
        update_data["course_duration"] = course_duration
    if course_duration_unit is not None:
        update_data["course_duration_unit"] = course_duration_unit
    if provider is not None:
        update_data["provider"] = provider
    if has_discount is not None:
        update_data["has_discount"] = has_discount
    if discount_requires_min_people is not None:
        update_data["discount_requires_min_people"] = discount_requires_min_people
    if discount_always_available is not None:
        update_data["discount_always_available"] = discount_always_available
    if discount_percentage is not None:
        update_data["discount_percentage"] = discount_percentage
    if discount_min_people is not None:
        update_data["discount_min_people"] = discount_min_people
    if course_type is not None:
        update_data["course_type"] = course_type
    if has_certificate is not None:
        update_data["has_certificate"] = has_certificate
    if certificate_type is not None:
        update_data["certificate_type"] = certificate_type
    if has_online_content is not None:
        update_data["has_online_content"] = has_online_content

    course_update = UpdateCourse(**update_data)
    return await CourseServices(db).update_course(id, course_update, images)


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
