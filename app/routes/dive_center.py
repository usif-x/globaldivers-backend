from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.dive_center import (
    DiveCenterCreate,
    DiveCenterResponse,
    DiveCenterUpdate,
)
from app.services.dive_center import DiveCenterService

dive_center_routes = APIRouter(prefix="/dive-centers", tags=["Dive Centers"])


@dive_center_routes.post(
    "/",
    response_model=DiveCenterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_dive_center(
    name: str = Form(...),
    description: str = Form(None),
    location: str = Form(...),
    hotel_name: str = Form(None),
    phone: str = Form(...),
    email: str = Form(...),
    working_hours: str = Form(None),
    image_files: list[UploadFile] = File(None),
    video_file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    # Parse working_hours JSON if provided
    import json

    wh = None
    if working_hours:
        try:
            wh = json.loads(working_hours)
        except Exception:
            wh = None
    data = DiveCenterCreate(
        name=name,
        description=description,
        location=location,
        hotel_name=hotel_name,
        phone=phone,
        email=email,
        working_hours=wh,
    )
    return await DiveCenterService(db).create_dive_center(
        data, image_files=image_files, video_file=video_file
    )


@dive_center_routes.get("/", response_model=List[DiveCenterResponse])
def get_all_dive_centers(db: Session = Depends(get_db)):
    return DiveCenterService(db).get_all_dive_centers()


@dive_center_routes.get("/{dive_center_id}", response_model=DiveCenterResponse)
def get_dive_center(dive_center_id: int, db: Session = Depends(get_db)):
    return DiveCenterService(db).get_dive_center_by_id(dive_center_id)


@dive_center_routes.put(
    "/{dive_center_id}",
    response_model=DiveCenterResponse,
    dependencies=[Depends(get_current_admin)],
)
def update_dive_center(
    dive_center_id: int, data: DiveCenterUpdate, db: Session = Depends(get_db)
):
    return DiveCenterService(db).update_dive_center(dive_center_id, data)


@dive_center_routes.delete(
    "/{dive_center_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_dive_center(dive_center_id: int, db: Session = Depends(get_db)):
    DiveCenterService(db).delete_dive_center(dive_center_id)
    return {"detail": "Deleted successfully"}
