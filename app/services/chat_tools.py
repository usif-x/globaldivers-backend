import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.best_selling import BestSelling, ItemType
from app.models.course import Course
from app.models.invoice import Invoice
from app.models.package import Package
from app.models.trip import Trip
from app.models.user import User

logger = logging.getLogger(__name__)


def get_best_selling_trips(db: Session, limit: int = 5) -> list[dict]:
    stmt = (
        select(Trip)
        .join(BestSelling, BestSelling.trip_id == Trip.id)
        .where(BestSelling.item_type == ItemType.TRIP)
        .order_by(BestSelling.ranking_position)
        .limit(limit)
    )
    trips = db.execute(stmt).scalars().all()
    return [_trip_to_dict(t) for t in trips]


def search_trips(
    db: Session,
    query: str = "",
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    limit: int = 10,
) -> list[dict]:
    stmt = select(Trip)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(Trip.name.ilike(like) | Trip.description.ilike(like))
    if price_min is not None:
        stmt = stmt.where(Trip.adult_price >= price_min)
    if price_max is not None:
        stmt = stmt.where(Trip.adult_price <= price_max)
    stmt = stmt.limit(limit)
    trips = db.execute(stmt).scalars().all()
    return [_trip_to_dict(t) for t in trips]


def get_packages(db: Session, trip_id: Optional[int] = None) -> list[dict]:
    if trip_id is not None:
        stmt = select(Package).where(Package.trips.any(id=trip_id))
    else:
        stmt = select(Package)
    packages = db.execute(stmt).scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": (p.description or "")[:500],
            "trip_count": len(p.trips),
        }
        for p in packages
    ]


def get_courses(db: Session) -> list[dict]:
    stmt = select(Course)
    courses = db.execute(stmt).scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": (c.description or "")[:500],
            "price": c.price if c.price_available else None,
            "level": c.course_level,
            "duration": c.course_duration,
            "duration_unit": c.course_duration_unit or "hours",
            "course_type": c.course_type,
            "provider": c.provider,
            "has_certificate": c.has_certificate,
            "certificate_type": c.certificate_type,
            "has_discount": c.has_discount,
            "discount_percentage": c.discount_percentage,
        }
        for c in courses
    ]


def get_user_profile(db: Session, user_id: int) -> Optional[dict]:
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalars().first()
    if not user:
        return None
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
    }


def get_user_invoices(db: Session, user_id: int) -> list[dict]:
    stmt = (
        select(Invoice)
        .where(Invoice.user_id == user_id)
        .order_by(Invoice.created_at.desc())
    )
    invoices = db.execute(stmt).scalars().all()
    return [
        {
            "id": inv.id,
            "activity": inv.activity,
            "amount": inv.amount,
            "currency": inv.currency,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "trip_id": inv.trip_id,
        }
        for inv in invoices
    ]


def _trip_to_dict(trip: Trip) -> dict:
    return {
        "id": trip.id,
        "name": trip.name,
        "description": (trip.description or "")[:500],
        "adult_price": trip.adult_price,
        "child_allowed": trip.child_allowed,
        "child_price": trip.child_price,
        "max_persons": trip.maxim_person,
        "duration": trip.duration,
        "duration_unit": trip.duration_unit,
        "has_discount": trip.has_discount,
        "discount_percentage": trip.discount_percentage,
        "included": trip.included,
        "not_included": trip.not_included,
    }
