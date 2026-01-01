# app/services/activity_availability.py

from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, delete
from sqlalchemy.orm import Session

from app.models.activity_availability import ActivityAvailability
from app.models.course import Course
from app.models.trip import Trip
from app.schemas.activity_availability import (
    ActivityAvailabilityCheckResponse,
    ActivityAvailabilityCreate,
    ActivityAvailabilityResponse,
    ActivityAvailabilityUpdate,
)


class ActivityAvailabilityService:
    @staticmethod
    def _validate_activity_exists(
        db: Session, activity_type: str, activity_id: int
    ) -> None:
        """
        Validate that the activity exists before creating availability record.

        Args:
            db: Database session
            activity_type: Type of activity ('trip' or 'course')
            activity_id: ID of the activity

        Raises:
            HTTPException: If activity doesn't exist
        """
        if activity_type == "trip":
            trip = db.query(Trip).filter(Trip.id == activity_id).first()
            if not trip:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trip with ID {activity_id} not found",
                )
        elif activity_type == "course":
            course = db.query(Course).filter(Course.id == activity_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Course with ID {activity_id} not found",
                )

    @staticmethod
    def close_activity_date(
        db: Session, data: ActivityAvailabilityCreate
    ) -> ActivityAvailabilityResponse:
        """
        Close an activity on a specific date by creating an availability record.

        Args:
            db: Database session
            data: Availability data (activity_type, activity_id, date, reason)

        Returns:
            Created availability record

        Raises:
            HTTPException: If activity doesn't exist or date already closed
        """
        # Validate activity exists
        ActivityAvailabilityService._validate_activity_exists(
            db, data.activity_type, data.activity_id
        )

        # Check if already closed
        existing = (
            db.query(ActivityAvailability)
            .filter(
                and_(
                    ActivityAvailability.activity_type == data.activity_type,
                    ActivityAvailability.activity_id == data.activity_id,
                    ActivityAvailability.date == data.date,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{data.activity_type.capitalize()} is already closed on {data.date}",
            )

        # Create availability record (closing the activity)
        availability = ActivityAvailability(
            activity_type=data.activity_type,
            activity_id=data.activity_id,
            date=data.date,
            reason=data.reason,
        )

        db.add(availability)
        db.commit()
        db.refresh(availability)

        return ActivityAvailabilityResponse.model_validate(availability)

    @staticmethod
    def reopen_activity_date(
        db: Session, activity_type: str, activity_id: int, target_date: date
    ) -> dict:
        """
        Reopen an activity on a specific date by deleting the availability record.

        Args:
            db: Database session
            activity_type: Type of activity ('trip' or 'course')
            activity_id: ID of the activity
            target_date: Date to reopen

        Returns:
            Success message

        Raises:
            HTTPException: If no closure record found
        """
        availability = (
            db.query(ActivityAvailability)
            .filter(
                and_(
                    ActivityAvailability.activity_type == activity_type,
                    ActivityAvailability.activity_id == activity_id,
                    ActivityAvailability.date == target_date,
                )
            )
            .first()
        )

        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No closure record found for {activity_type} {activity_id} on {target_date}",
            )

        db.delete(availability)
        db.commit()

        return {
            "message": f"{activity_type.capitalize()} {activity_id} reopened for {target_date}"
        }

    @staticmethod
    def update_closed_date(
        db: Session,
        availability_id: int,
        data: ActivityAvailabilityUpdate,
    ) -> ActivityAvailabilityResponse:
        """
        Update an existing closure record (change the date or reason).

        Args:
            db: Database session
            availability_id: ID of the availability record
            data: Updated data (new date and/or reason)

        Returns:
            Updated availability record

        Raises:
            HTTPException: If record not found or new date conflicts
        """
        availability = (
            db.query(ActivityAvailability)
            .filter(ActivityAvailability.id == availability_id)
            .first()
        )

        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability record not found",
            )

        # Check if new date conflicts with existing record
        if data.date != availability.date:
            existing = (
                db.query(ActivityAvailability)
                .filter(
                    and_(
                        ActivityAvailability.activity_type
                        == availability.activity_type,
                        ActivityAvailability.activity_id == availability.activity_id,
                        ActivityAvailability.date == data.date,
                    )
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Activity already closed on {data.date}",
                )

        # Update record
        availability.date = data.date
        if data.reason is not None:
            availability.reason = data.reason

        db.commit()
        db.refresh(availability)

        return ActivityAvailabilityResponse.model_validate(availability)

    @staticmethod
    def check_availability(
        db: Session, activity_type: str, activity_id: int, target_date: date
    ) -> ActivityAvailabilityCheckResponse:
        """
        Check if an activity is available on a specific date.

        Args:
            db: Database session
            activity_type: Type of activity ('trip' or 'course')
            activity_id: ID of the activity
            target_date: Date to check

        Returns:
            Availability status with reason if closed
        """
        closure = (
            db.query(ActivityAvailability)
            .filter(
                and_(
                    ActivityAvailability.activity_type == activity_type,
                    ActivityAvailability.activity_id == activity_id,
                    ActivityAvailability.date == target_date,
                )
            )
            .first()
        )

        if closure:
            return ActivityAvailabilityCheckResponse(
                is_available=False,
                reason=closure.reason,
                message=f"{activity_type.capitalize()} is closed on {target_date}",
            )

        return ActivityAvailabilityCheckResponse(
            is_available=True,
            reason=None,
            message=f"{activity_type.capitalize()} is available on {target_date}",
        )

    @staticmethod
    def get_all_closures(
        db: Session,
        activity_type: Optional[str] = None,
        activity_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ActivityAvailabilityResponse]:
        """
        Get all closure records with optional filters.

        Args:
            db: Database session
            activity_type: Filter by activity type (optional)
            activity_id: Filter by activity ID (optional)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of availability records
        """
        query = db.query(ActivityAvailability)

        if activity_type:
            query = query.filter(ActivityAvailability.activity_type == activity_type)

        if activity_id:
            query = query.filter(ActivityAvailability.activity_id == activity_id)

        # Only show future and today's closures
        query = query.filter(ActivityAvailability.date >= date.today())

        availabilities = (
            query.order_by(ActivityAvailability.date.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [ActivityAvailabilityResponse.model_validate(a) for a in availabilities]

    @staticmethod
    def cleanup_past_closures(db: Session) -> dict:
        """
        Delete all availability records for dates in the past.
        This should be called by a scheduled job daily.

        Args:
            db: Database session

        Returns:
            Number of records deleted
        """
        result = db.execute(
            delete(ActivityAvailability).where(ActivityAvailability.date < date.today())
        )
        db.commit()

        deleted_count = result.rowcount

        return {
            "message": f"Cleaned up {deleted_count} past availability records",
            "deleted_count": deleted_count,
        }
