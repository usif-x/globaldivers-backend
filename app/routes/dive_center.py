import json
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
    coordinates: str = Form(None),
    images: list[UploadFile] = File(None),  # was image_files
    video: UploadFile = File(None),  # was video_file
    db: Session = Depends(get_db),
):
    wh = None
    if working_hours:
        try:
            wh = json.loads(working_hours)
        except Exception:
            wh = None

    coords = None
    if coordinates:
        try:
            coords = json.loads(coordinates)
        except Exception:
            coords = None

    data = DiveCenterCreate(
        name=name,
        description=description,
        location=location,
        hotel_name=hotel_name,
        phone=phone,
        email=email,
        working_hours=wh,
        coordinates=coords,
    )
    return await DiveCenterService(db).create_dive_center(
        data, image_files=images, video_file=video
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
async def update_dive_center(
    dive_center_id: int,
    name: str = Form(None),
    description: str = Form(None),
    location: str = Form(None),
    hotel_name: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    working_hours: str = Form(None),
    is_image_list: bool = Form(None),
    replace_images: bool = Form(False),
    images: list[UploadFile] = File(None),  # was image_files
    video: UploadFile = File(None),  # confirm this is the wire name too
    db: Session = Depends(get_db),
):
    wh = None
    if working_hours:
        try:
            wh = json.loads(working_hours)
        except Exception:
            wh = None

    raw = {
        "name": name,
        "description": description,
        "location": location,
        "hotel_name": hotel_name,
        "phone": phone,
        "email": email,
        "working_hours": wh,
        "is_image_list": is_image_list,
    }
    # only keep fields actually sent, so we don't null out untouched columns
    provided = {k: v for k, v in raw.items() if v is not None}
    data = DiveCenterUpdate(**provided)

    return await DiveCenterService(db).update_dive_center(
        dive_center_id,
        data,
        image_files=images,  # map to whatever service expects
        video_file=video,
        replace_images=replace_images,
    )


@dive_center_routes.delete(
    "/{dive_center_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_dive_center(dive_center_id: int, db: Session = Depends(get_db)):
    DiveCenterService(db).delete_dive_center(dive_center_id)
