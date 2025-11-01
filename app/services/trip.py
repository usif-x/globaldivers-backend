from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception_handler import db_exception_handler
from app.models.trip import Trip
from app.schemas.trip import CreateTrip, TripResponse, UpdateTrip
from app.utils.upload_img import delete_uploaded_image, upload_images


class TripServices:
    def __init__(self, db: Session):
        self.db = db

    def _convert_filenames_to_urls(self, filenames: List[str]) -> List[str]:
        """Convert image filenames to full URLs"""
        if not filenames:
            return []

        base_url = settings.APP_URL.rstrip("/")
        return [f"{base_url}/storage/images/{filename}" for filename in filenames]

    def _extract_filenames_from_urls(self, urls: List[str]) -> List[str]:
        """Extract filenames from full URLs (for delete operations)"""
        if not urls:
            return []

        filenames = []
        for url in urls:
            if "/storage/images/" in url:
                filename = url.split("/storage/images/")[-1]
                filenames.append(filename)
        return filenames

    @db_exception_handler
    async def create_trip(self, trip: CreateTrip, images: List[UploadFile] = None):
        # Upload images if provided
        image_filenames = []
        if images:
            try:
                # Upload all images and get their filenames
                image_filenames = await upload_images(images)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload images: {str(e)}"
                )

        # Create trip with uploaded image filenames
        trip_data = trip.model_dump()
        trip_data["images"] = image_filenames

        new_trip = Trip(**trip_data)
        self.db.add(new_trip)
        self.db.commit()
        self.db.refresh(new_trip)

        # Convert filenames to full URLs before returning
        new_trip.images = self._convert_filenames_to_urls(new_trip.images)
        return new_trip

    @db_exception_handler
    def get_all_trips(self):
        stmt = select(Trip)
        trips = self.db.execute(stmt).scalars().all()

        # Convert filenames to full URLs for all trips
        for trip in trips:
            trip.images = self._convert_filenames_to_urls(trip.images)

        return trips

    @db_exception_handler
    def get_trip_by_id(self, id: int):
        stmt = select(Trip).where(Trip.id == id)
        trip = self.db.execute(stmt).scalars().first()
        if trip:
            # Convert filenames to full URLs
            trip.images = self._convert_filenames_to_urls(trip.images)
            return TripResponse.model_validate(trip, from_attributes=True)
        else:
            raise HTTPException(404, detail="Trip not found")

    @db_exception_handler
    def delete_trip(self, id: int):
        try:
            stmt = select(Trip).where(Trip.id == id)
            trip = self.db.execute(stmt).scalars().first()
            if trip:
                # Delete associated images from storage
                if trip.images:
                    # Extract filenames from URLs if needed
                    filenames_to_delete = (
                        self._extract_filenames_from_urls(trip.images)
                        if trip.images
                        and "/storage/images/"
                        in (trip.images[0] if trip.images else "")
                        else trip.images
                    )

                    for image_filename in filenames_to_delete:
                        try:
                            delete_uploaded_image(image_filename)
                        except Exception as e:
                            print(f"Failed to delete image {image_filename}: {e}")

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
            # Handle image updates
            if images:
                try:
                    # Delete old images from storage
                    if updated_trip.images:
                        # Extract filenames from URLs if needed
                        old_filenames = (
                            self._extract_filenames_from_urls(updated_trip.images)
                            if updated_trip.images
                            and "/storage/images/"
                            in (updated_trip.images[0] if updated_trip.images else "")
                            else updated_trip.images
                        )

                        for old_image in old_filenames:
                            try:
                                delete_uploaded_image(old_image)
                            except Exception as e:
                                print(f"Failed to delete old image {old_image}: {e}")

                    # Upload new images
                    new_image_filenames = await upload_images(images)

                    # Update trip data
                    data = trip.model_dump(exclude_unset=True)
                    data["images"] = new_image_filenames

                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Failed to upload new images: {str(e)}"
                    )
            else:
                # No new images, just update other fields
                data = trip.model_dump(exclude_unset=True)

            # Apply updates
            for field, value in data.items():
                setattr(updated_trip, field, value)

            self.db.commit()
            self.db.refresh(updated_trip)

            # Convert filenames to full URLs before returning
            updated_trip.images = self._convert_filenames_to_urls(updated_trip.images)

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
            # Get all trips to delete their images
            trips = self.db.execute(select(Trip)).scalars().all()

            # Delete all associated images from storage
            for trip in trips:
                if trip.images:
                    # Extract filenames from URLs if needed
                    filenames_to_delete = (
                        self._extract_filenames_from_urls(trip.images)
                        if trip.images
                        and "/storage/images/"
                        in (trip.images[0] if trip.images else "")
                        else trip.images
                    )

                    for image_filename in filenames_to_delete:
                        try:
                            delete_uploaded_image(image_filename)
                        except Exception as e:
                            print(f"Failed to delete image {image_filename}: {e}")

            # Delete all trips from database
            self.db.execute(delete(Trip))
            self.db.commit()
            return {"success": True, "message": "All trips deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting trips: {str(e)}"}
