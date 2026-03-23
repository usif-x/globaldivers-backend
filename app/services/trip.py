from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.trip import Trip
from app.schemas.trip import CreateTrip, TripResponse, UpdateTrip
from app.utils.storage import delete_file, get_public_url
from app.utils.upload_img import upload_images


class TripServices:
    def __init__(self, db: Session):
        self.db = db

    def _convert_keys_to_urls(self, keys: List[str]) -> List[str]:
        """Convert S3 object keys to full public URLs."""
        if not keys:
            return []
        return [get_public_url(key) for key in keys]

    @db_exception_handler
    async def create_trip(self, trip: CreateTrip, images: List[UploadFile] = None):
        # Upload images if provided
        image_keys = []
        if images:
            try:
                image_keys = await upload_images(images)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload images: {str(e)}"
                )

        trip_data = trip.model_dump()
        trip_data["images"] = image_keys

        new_trip = Trip(**trip_data)
        self.db.add(new_trip)
        self.db.commit()
        self.db.refresh(new_trip)

        new_trip.images = self._convert_keys_to_urls(new_trip.images)
        return new_trip

    @db_exception_handler
    def get_all_trips(self):
        stmt = select(Trip)
        trips = self.db.execute(stmt).scalars().all()

        for trip in trips:
            trip.images = self._convert_keys_to_urls(trip.images)

        return trips

    @db_exception_handler
    def get_trip_by_id(self, id: int):
        stmt = select(Trip).where(Trip.id == id)
        trip = self.db.execute(stmt).scalars().first()
        if trip:
            trip.images = self._convert_keys_to_urls(trip.images)
            return TripResponse.model_validate(trip, from_attributes=True)
        else:
            raise HTTPException(404, detail="Trip not found")

    @db_exception_handler
    def delete_trip(self, id: int):
        try:
            stmt = select(Trip).where(Trip.id == id)
            trip = self.db.execute(stmt).scalars().first()
            if trip:
                if trip.images:
                    for key in trip.images:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete image {key}: {e}")

                self.db.delete(trip)
                self.db.commit()
                return {"success": True, "message": "Trip deleted successfully"}
            else:
                raise HTTPException(404, detail="Trip not found")
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting trip: {str(e)}"}

    @db_exception_handler
    async def update_trip(
        self, trip: UpdateTrip, id: int, images: List[UploadFile] = None
    ):
        stmt = select(Trip).where(Trip.id == id)
        updated_trip = self.db.execute(stmt).scalars().first()
        if updated_trip:
            if images:
                try:
                    # Delete old images from S3
                    if updated_trip.images:
                        for old_key in updated_trip.images:
                            try:
                                delete_file(old_key)
                            except Exception as e:
                                print(f"Failed to delete old image {old_key}: {e}")

                    # Upload new images
                    new_image_keys = await upload_images(images)

                    data = trip.model_dump(exclude_unset=True)
                    data["images"] = new_image_keys

                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Failed to upload new images: {str(e)}"
                    )
            else:
                data = trip.model_dump(exclude_unset=True)

            for field, value in data.items():
                setattr(updated_trip, field, value)

            self.db.commit()
            self.db.refresh(updated_trip)

            updated_trip.images = self._convert_keys_to_urls(updated_trip.images)

            return {
                "success": True,
                "message": "Trip Updated successfully",
                "trip": TripResponse.model_validate(updated_trip, from_attributes=True),
            }
        else:
            raise HTTPException(404, detail="Trip not found")

    @db_exception_handler
    def delete_all_trips(self):
        try:
            trips = self.db.execute(select(Trip)).scalars().all()

            for trip in trips:
                if trip.images:
                    for key in trip.images:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete image {key}: {e}")

            self.db.execute(delete(Trip))
            self.db.commit()
            return {"success": True, "message": "All trips deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting trips: {str(e)}"}
