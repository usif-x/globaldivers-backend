from typing import List

from fastapi import APIRouter, Depends, File, Form, Path, UploadFile
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.trip import CreateTrip, TripResponse, UpdateTrip
from app.services.trip import TripServices

from fastapi.concurrency import run_in_threadpool

trip_routes = APIRouter(prefix="/trips", tags=["Trip Endpoints"])

@trip_routes.get("/", response_model=list[TripResponse])
@cache(expire=600)
async def get_all_trips(db: Session = Depends(get_db)):
    return await run_in_threadpool(TripServices(db).get_all_trips)


@trip_routes.post("/", response_model=TripResponse, dependencies=[Depends(get_current_admin)])
async def create_trip(
    name: str = Form(...),
    description: str = Form(...),
    is_image_list: bool = Form(False),
    adult_price: float = Form(...),
    child_allowed: bool = Form(...),
    child_price: float = Form(...),
    maxim_person: int = Form(...),
    has_discount: bool = Form(False),
    discount_requires_min_people: bool = Form(False),
    discount_always_available: bool = Form(False),
    discount_min_people: int = Form(0),
    discount_percentage: float = Form(0.0),
    duration: int = Form(...),
    duration_unit: str = Form(...),
    package_id: int = Form(...),
    included: List[str] = Form(...),
    not_included: List[str] = Form(...),
    terms_and_conditions: List[str] = Form(...),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Create trip object from form data
    trip_data = CreateTrip(
        name=name,
        description=description,
        images=[],  # Will be filled by the service
        is_image_list=is_image_list,
        adult_price=adult_price,
        child_allowed=child_allowed,
        child_price=child_price,
        maxim_person=maxim_person,
        has_discount=has_discount,
        discount_requires_min_people=discount_requires_min_people,
        discount_always_available=discount_always_available,
        discount_min_people=discount_min_people,
        discount_percentage=discount_percentage,
        duration=duration,
        duration_unit=duration_unit,
        package_id=package_id,
        included=included,
        not_included=not_included,
        terms_and_conditions=terms_and_conditions,
    )

    return await TripServices(db).create_trip(trip_data, images)


@trip_routes.get("/{id}", response_model=TripResponse)
async def get_trip_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return await run_in_threadpool(TripServices(db).get_trip_by_id, id)


@trip_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_trip(id: int, db: Session = Depends(get_db)):
    return await run_in_threadpool(TripServices(db).delete_trip, id)


@trip_routes.put("/{id}", dependencies=[Depends(get_current_admin)])
async def update_trip(
    id: int,
    name: str = Form(None),
    description: str = Form(None),
    is_image_list: bool = Form(None),
    adult_price: float = Form(None),
    child_allowed: bool = Form(None),
    child_price: float = Form(None),
    maxim_person: int = Form(None),
    has_discount: bool = Form(None),
    discount_requires_min_people: bool = Form(None),
    discount_always_available: bool = Form(None),
    discount_min_people: int = Form(None),
    discount_percentage: float = Form(None),
    duration: int = Form(None),
    duration_unit: str = Form(None),
    package_id: int = Form(None),
    included: List[str] = Form(None),
    not_included: List[str] = Form(None),
    terms_and_conditions: List[str] = Form(None),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    params = locals()
    excluded = {"id", "images", "db"}
    update_data = {k: v for k, v in params.items() if k not in excluded and v is not None}
    
    trip_update = UpdateTrip(**update_data)
    return await TripServices(db).update_trip(trip_update, id, images)
