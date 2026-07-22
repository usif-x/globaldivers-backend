from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.experience import ExperienceResponse
from app.services.experience import ExperienceService

experience_routes = APIRouter(prefix="/experiences", tags=["Experiences"])


@experience_routes.post(
    "/",
    response_model=ExperienceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_experience(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await ExperienceService(db).create_experience(file)


@experience_routes.get("/", response_model=List[ExperienceResponse])
def get_all_experiences(db: Session = Depends(get_db)):
    return ExperienceService(db).get_all_experiences()


@experience_routes.delete(
    "/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_experience(experience_id: int, db: Session = Depends(get_db)):
    ExperienceService(db).delete_experience(experience_id)
