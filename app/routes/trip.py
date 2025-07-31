from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.trip import CreateTrip, TripResponse, UpdateTrip
from app.services.trip import TripServices

trip_routes = APIRouter(prefix="/trips", tags=["Trip Endpoints"])


@trip_routes.get("/", response_model=list[TripResponse])
async def get_all_trips(db: Session = Depends(get_db)):
    return TripServices(db).get_all_trips()


@trip_routes.post(
    "/", response_model=TripResponse, dependencies=[Depends(get_current_admin)]
)
async def create_trip(trip: CreateTrip, db: Session = Depends(get_db)):
    return TripServices(db).create_trip(trip)


@trip_routes.get("/{id}", response_model=TripResponse)
async def get_trip_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return TripServices(db).get_trip_by_id(id)


@trip_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_trip(id: int, db: Session = Depends(get_db)):
    return TripServices(db).delete_trip(id)


@trip_routes.put("/{id}", dependencies=[Depends(get_current_admin)])
async def update_trip(trip: UpdateTrip, id: int, db: Session = Depends(get_db)):
    return TripServices(db).update_trip(trip, id)
