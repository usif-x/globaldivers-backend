from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.fee import TripFee
from app.models.transfer import TripTransferFee
from app.models.trip import Trip
from app.schemas.trip import CreateTrip, TripResponse, UpdateTrip
from app.utils.storage import delete_file, get_public_url
from app.utils.upload_img import upload_images
from app.utils.upload_video import upload_videos


class TripServices:
    def __init__(self, db: Session):
        self.db = db

    def _convert_keys_to_urls(self, keys: List[str]) -> List[str]:
        """Convert S3 object keys to full public URLs."""
        if not keys:
            return []
        return [get_public_url(key) for key in keys]

    def _sync_fees(self, trip_id: int, fees: list):
        """Replace all fee rows for a trip with the given list."""
        self.db.execute(delete(TripFee).where(TripFee.trip_id == trip_id))
        for fee in fees:
            self.db.add(TripFee(trip_id=trip_id, **fee))

    def _sync_transfer_fees(self, trip_id: int, transfer_fees: list):
        """Replace all transfer fee rows for a trip with the given list."""
        self.db.execute(
            delete(TripTransferFee).where(TripTransferFee.trip_id == trip_id)
        )
        for tf in transfer_fees:
            self.db.add(TripTransferFee(trip_id=trip_id, **tf))

    @db_exception_handler
    async def create_trip(
        self,
        trip: CreateTrip,
        images: List[UploadFile] = None,
        videos: List[UploadFile] = None,
    ):
        image_keys = []
        if images:
            try:
                image_keys = await upload_images(images)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload images: {str(e)}"
                )

        video_keys = []
        if videos:
            try:
                video_keys = await upload_videos(videos)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload videos: {str(e)}"
                )

        trip_data = trip.model_dump()
        trip_data["images"] = image_keys
        trip_data["videos"] = video_keys

        # fees/transfer_fees are nested relationships, not columns on Trip
        fees = trip_data.pop("fees", [])
        transfer_fees = trip_data.pop("transfer_fees", [])

        new_trip = Trip(**trip_data)
        self.db.add(new_trip)
        self.db.flush()  # assigns new_trip.id without committing yet

        for fee in fees:
            self.db.add(TripFee(trip_id=new_trip.id, **fee))

        for tf in transfer_fees:
            self.db.add(TripTransferFee(trip_id=new_trip.id, **tf))

        self.db.commit()
        self.db.refresh(new_trip)

        new_trip.images = self._convert_keys_to_urls(new_trip.images)
        new_trip.videos = self._convert_keys_to_urls(new_trip.videos)
        return new_trip

    @db_exception_handler
    def get_all_trips(self):
        stmt = select(Trip)
        trips = self.db.execute(stmt).scalars().all()

        for trip in trips:
            trip.images = self._convert_keys_to_urls(trip.images)
            trip.videos = self._convert_keys_to_urls(trip.videos)

        return trips

    @db_exception_handler
    def get_trip_by_id(self, id: int):
        stmt = select(Trip).where(Trip.id == id)
        trip = self.db.execute(stmt).scalars().first()
        if trip:
            trip.images = self._convert_keys_to_urls(trip.images)
            trip.videos = self._convert_keys_to_urls(trip.videos)
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

                if trip.videos:
                    for key in trip.videos:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete video {key}: {e}")

                # fees/transfer_fees rely on ondelete="CASCADE" on the FK,
                # so deleting the trip cleans them up automatically.
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
        self,
        trip: UpdateTrip,
        id: int,
        images: List[UploadFile] = None,
        videos: List[UploadFile] = None,
    ):
        stmt = select(Trip).where(Trip.id == id)
        updated_trip = self.db.execute(stmt).scalars().first()
        if updated_trip:
            data = trip.model_dump(exclude_unset=True)

            # fees/transfer_fees need separate handling — they're relationships
            fees = data.pop("fees", None)
            transfer_fees = data.pop("transfer_fees", None)

            if images:
                try:
                    if updated_trip.images:
                        for old_key in updated_trip.images:
                            try:
                                delete_file(old_key)
                            except Exception as e:
                                print(f"Failed to delete old image {old_key}: {e}")

                    data["images"] = await upload_images(images)
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Failed to upload new images: {str(e)}"
                    )

            if videos:
                try:
                    if updated_trip.videos:
                        for old_key in updated_trip.videos:
                            try:
                                delete_file(old_key)
                            except Exception as e:
                                print(f"Failed to delete old video {old_key}: {e}")

                    data["videos"] = await upload_videos(videos)
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Failed to upload new videos: {str(e)}"
                    )

            for field, value in data.items():
                setattr(updated_trip, field, value)

            # only touch fees if the client actually sent them
            if fees is not None:
                self._sync_fees(updated_trip.id, fees)

            if transfer_fees is not None:
                self._sync_transfer_fees(updated_trip.id, transfer_fees)

            self.db.commit()
            self.db.refresh(updated_trip)

            updated_trip.images = self._convert_keys_to_urls(updated_trip.images)
            updated_trip.videos = self._convert_keys_to_urls(updated_trip.videos)

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

                if trip.videos:
                    for key in trip.videos:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete video {key}: {e}")

            self.db.execute(delete(Trip))
            self.db.commit()
            return {"success": True, "message": "All trips deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting trips: {str(e)}"}
