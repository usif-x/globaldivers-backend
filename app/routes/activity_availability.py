# app/routes/activity_availability.py

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user, get_db
from app.schemas.activity_availability import (
    ActivityAvailabilityCheckRequest,
    ActivityAvailabilityCheckResponse,
    ActivityAvailabilityCreate,
    ActivityAvailabilityResponse,
    ActivityAvailabilityUpdate,
)
from app.services.activity_availability import ActivityAvailabilityService

router = APIRouter(prefix="/activity-availability", tags=["Activity Availability"])


@router.post(
    "/close",
    response_model=ActivityAvailabilityResponse,
    summary="Close activity on specific date (Admin)",
)
def close_activity_date(
    data: ActivityAvailabilityCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user),
):
    """
    Close an activity (trip/course) on a specific date.
    Creates an availability record indicating the activity is closed.

    **Admin only**
    """
    return ActivityAvailabilityService.close_activity_date(db, data)


@router.delete(
    "/reopen",
    summary="Reopen activity on specific date (Admin)",
)
def reopen_activity_date(
    activity_type: str = Query(..., pattern="^(trip|course)$"),
    activity_id: int = Query(..., gt=0),
    date: date = Query(...),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user),
):
    """
    Reopen an activity (trip/course) on a specific date.
    Deletes the availability record, making the activity available again.

    **Admin only**
    """
    return ActivityAvailabilityService.reopen_activity_date(
        db, activity_type, activity_id, date
    )


@router.patch(
    "/{availability_id}",
    response_model=ActivityAvailabilityResponse,
    summary="Update closure date (Admin)",
)
def update_closure_date(
    availability_id: int,
    data: ActivityAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user),
):
    """
    Update an existing closure record (change the date or reason).

    **Admin only**
    """
    return ActivityAvailabilityService.update_closed_date(db, availability_id, data)


@router.get(
    "/check",
    response_model=ActivityAvailabilityCheckResponse,
    summary="Check if activity is available",
)
def check_availability(
    activity_type: str = Query(..., pattern="^(trip|course)$"),
    activity_id: int = Query(..., gt=0),
    date: date = Query(...),
    db: Session = Depends(get_db),
):
    """
    Check if an activity is available on a specific date.

    Returns:
    - `is_available: true` if activity is open
    - `is_available: false` if activity is closed (with reason if provided)

    **Public endpoint** - no authentication required
    """
    return ActivityAvailabilityService.check_availability(
        db, activity_type, activity_id, date
    )


@router.get(
    "/",
    response_model=List[ActivityAvailabilityResponse],
    summary="Get all closures (Admin)",
)
def get_all_closures(
    activity_type: Optional[str] = Query(None, pattern="^(trip|course)$"),
    activity_id: Optional[int] = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user),
):
    """
    Get all activity closure records.
    Supports filtering by activity_type and activity_id.

    **Admin only**
    """
    return ActivityAvailabilityService.get_all_closures(
        db, activity_type, activity_id, skip, limit
    )


@router.post(
    "/cleanup",
    summary="Cleanup past closures (Admin/Cron)",
)
def cleanup_past_closures(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user),
):
    """
    Delete all availability records for past dates.
    This endpoint should be called by a scheduled job daily.

    **Admin only** (or configure for internal cron job)
    """
    return ActivityAvailabilityService.cleanup_past_closures(db)
