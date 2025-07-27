from fastapi import APIRouter, Depends, Path
from app.services.course import CourseServices
from app.schemas.course import CreateCourse, CourseResponse, UpdateCourse
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_admin




course_routes = APIRouter(
  prefix="/courses",
  tags=["Course Endpoints"]
)



@course_routes.get("/", response_model=list[CourseResponse])
async def get_all_courses(db: Session = Depends(get_db)):
    return CourseServices(db).get_all_courses()



@course_routes.get("/{id}", response_model=CourseResponse)
async def get_course_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return CourseServices(db).get_course_by_id(id)


@course_routes.post("/", response_model=CourseResponse, dependencies=[Depends(get_current_admin)])
async def create_course(course: CreateCourse, db: Session = Depends(get_db)):
    return CourseServices(db).create_course(course)


@course_routes.put("/{id}", response_model=CourseResponse, dependencies=[Depends(get_current_admin)])
async def update_course(course: UpdateCourse, id: int, db: Session = Depends(get_db)):
    return CourseServices(db).update_course(id, course)



@course_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_course(id: int, db: Session = Depends(get_db)):
    return CourseServices(db).delete_course(id)


@course_routes.delete("/delete-all", dependencies=[Depends(get_current_admin)])
async def delete_all_courses(db: Session = Depends(get_db)):
    return CourseServices(db).delete_all_courses()


