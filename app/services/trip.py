from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.trip import Trip
from app.schemas.trip import CreateTrip, TripResponse, UpdateTrip



class TripServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_trip(self, trip: CreateTrip):
        new_trip = Trip(**trip.model_dump())
        self.db.add(new_trip)
        self.db.commit()
        self.db.refresh(new_trip)
        return new_trip

    @db_exception_handler
    def get_all_trips(self):
        stmt = select(Trip)
        trips = self.db.execute(stmt).scalars().all()
        return trips

    @db_exception_handler
    def get_trip_by_id(self, id: int):
        stmt = select(Trip).where(Trip.id == id)
        trip = self.db.execute(stmt).scalars().first()
        if trip:
            return TripResponse.model_validate(trip, from_attributes=True)
        else:
            raise HTTPException(404, detail="Trip not found")

    @db_exception_handler
    def delete_trip(self, id: int):
        stmt = select(Trip).where(Trip.id == id)
        trip = self.db.execute(stmt).scalars().first()
        if trip:
            self.db.delete(trip)
            self.db.commit()
            return {"success": True, "message": "Trip deleted successfully"}
        else:
            raise HTTPException(404, detail="Trip not found")

    @db_exception_handler
    def update_trip(self, trip: UpdateTrip, id: int):
        stmt = select(Trip).where(Trip.id == id)
        updated_trip = self.db.execute(stmt).scalars().first()
        if updated_trip:
            data = trip.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(updated_trip, field, value)
            self.db.commit()
            self.db.refresh(updated_trip)
            return {
                "success": True,
                "message": "Trip Updated successfuly",
                "trip": TripResponse.model_validate(updated_trip, from_attributes=True),
            }
        else:
            raise HTTPException(404, detail="Trip not found")

    @db_exception_handler
    def delete_all_trips(self):
        try:
            self.db.execute(delete(Trip))
            self.db.commit()
            return {"success": True, "message": "All trips deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting trips: {str(e)}"}
