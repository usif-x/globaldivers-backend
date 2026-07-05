import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_availability import ActivityAvailability
from app.models.best_selling import BestSelling, ItemType
from app.models.blog import Blog
from app.models.bundle import TripBundleOffer
from app.models.coupon import Coupon
from app.models.course import Course
from app.models.course_content import CourseContent
from app.models.dive_center import DiveCenter
from app.models.fee import TripFee
from app.models.gallery import Gallery
from app.models.invoice import Invoice
from app.models.notification import Notification
from app.models.package import Package
from app.models.public_notification import PublicNotification
from app.models.setting import WebsiteSettings
from app.models.testimonial import Testimonial
from app.models.transfer import TransferZone, TripTransferFee
from app.models.trip import Trip
from app.models.user import User

logger = logging.getLogger(__name__)


# =============================================================================
# Trip Tools
# =============================================================================


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


def get_best_selling_courses(db: Session, limit: int = 5) -> list[dict]:
    stmt = (
        select(Course)
        .join(BestSelling, BestSelling.course_id == Course.id)
        .where(BestSelling.item_type == ItemType.COURSE)
        .order_by(BestSelling.ranking_position)
        .limit(limit)
    )
    courses = db.execute(stmt).scalars().all()
    return [_course_to_dict(c) for c in courses]


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


def get_trip_by_id(db: Session, trip_id: int) -> Optional[dict]:
    stmt = select(Trip).where(Trip.id == trip_id)
    trip = db.execute(stmt).scalars().first()
    if not trip:
        return None
    return {
        **_trip_to_dict(trip),
        "included": trip.included,
        "not_included": trip.not_included,
        "terms_and_conditions": trip.terms_and_conditions,
        "images": trip.images,
        "child_allowed": trip.child_allowed,
        "child_price": trip.child_price,
        "maxim_person": trip.maxim_person,
        "discount_requires_min_people": trip.discount_requires_min_people,
        "discount_always_available": trip.discount_always_available,
        "discount_min_people": trip.discount_min_people,
    }


def get_trip_fees(db: Session, trip_id: int) -> list[dict]:
    stmt = select(TripFee).where(TripFee.trip_id == trip_id)
    fees = db.execute(stmt).scalars().all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "fee_type": f.fee_type,
            "value": f.value,
            "applies_to": f.applies_to,
            "is_optional": f.is_optional,
            "is_included_in_price": f.is_included_in_price,
            "description": f.description,
        }
        for f in fees
    ]


def get_transfer_zones(db: Session) -> list[dict]:
    stmt = select(TransferZone).order_by(TransferZone.name)
    zones = db.execute(stmt).scalars().all()
    return [
        {
            "id": z.id,
            "name": z.name,
            "region": z.region,
        }
        for z in zones
    ]


def get_trip_transfer_fees(db: Session, trip_id: int) -> list[dict]:
    stmt = (
        select(TripTransferFee)
        .where(TripTransferFee.trip_id == trip_id)
        .order_by(TripTransferFee.zone_id)
    )
    fees = db.execute(stmt).scalars().all()
    return [
        {
            "id": f.id,
            "zone_id": f.zone_id,
            "zone_name": f.zone.name if f.zone else None,
            "fee_type": f.fee_type,
            "price": f.price,
            "applies_to": f.applies_to,
        }
        for f in fees
    ]


# =============================================================================
# Course Tools
# =============================================================================


def get_courses(db: Session) -> list[dict]:
    stmt = select(Course)
    courses = db.execute(stmt).scalars().all()
    return [_course_to_dict(c) for c in courses]


def get_course_by_id(db: Session, course_id: int) -> Optional[dict]:
    stmt = select(Course).where(Course.id == course_id)
    course = db.execute(stmt).scalars().first()
    if not course:
        return None
    return {
        **_course_to_dict(course),
        "description": course.description or "",
        "images": course.images,
        "has_online_content": course.has_online_content,
        "price_available": course.price_available,
        "discount_requires_min_people": course.discount_requires_min_people,
        "discount_always_available": course.discount_always_available,
        "discount_min_people": course.discount_min_people,
    }


def search_courses(
    db: Session,
    query: str = "",
    level: Optional[str] = None,
    course_type: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    stmt = select(Course)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(Course.name.ilike(like) | Course.description.ilike(like))
    if level:
        stmt = stmt.where(Course.course_level.ilike(f"%{level}%"))
    if course_type:
        stmt = stmt.where(Course.course_type.ilike(f"%{course_type}%"))
    if provider:
        stmt = stmt.where(Course.provider.ilike(f"%{provider}%"))
    stmt = stmt.limit(limit)
    courses = db.execute(stmt).scalars().all()
    return [_course_to_dict(c) for c in courses]


# =============================================================================
# Package Tools
# =============================================================================


def get_packages(db: Session, trip_id: Optional[int] = None) -> list[dict]:
    if trip_id is not None:
        stmt = select(Package).where(Package.trips.any(id=trip_id))
    else:
        stmt = select(Package)
    packages = db.execute(stmt).scalars().all()
    return [_package_to_dict(p) for p in packages]


def get_package_by_id(db: Session, package_id: int) -> Optional[dict]:
    stmt = select(Package).where(Package.id == package_id)
    package = db.execute(stmt).scalars().first()
    if not package:
        return None
    trips = [_trip_to_dict(t) for t in package.trips] if package.trips else []
    return {
        **_package_to_dict(package),
        "description": package.description or "",
        "trips": trips,
    }


# =============================================================================
# Bundle Tools
# =============================================================================


def get_bundle_offers(db: Session, trip_id: Optional[int] = None) -> list[dict]:
    stmt = select(TripBundleOffer).where(TripBundleOffer.is_active.is_(True))
    if trip_id is not None:
        stmt = stmt.where(TripBundleOffer.required_trips.any(id=trip_id))
    offers = db.execute(stmt).scalars().all()
    now = datetime.utcnow()
    return [
        {
            "id": o.id,
            "name": o.name,
            "description": o.description or "",
            "discount_type": o.discount_type,
            "discount_value": o.discount_value,
            "min_required_trips": o.min_required_trips,
            "offer_trip_name": o.offer_trip.name if o.offer_trip else None,
            "valid_from": o.valid_from.isoformat() if o.valid_from else None,
            "valid_until": o.valid_until.isoformat() if o.valid_until else None,
            "is_valid_now": (not o.valid_from or o.valid_from <= now) and (not o.valid_until or o.valid_until >= now),
        }
        for o in offers
    ]


# =============================================================================
# Dive Center & Settings Tools
# =============================================================================


def get_dive_center_info(db: Session) -> Optional[dict]:
    dive_center = db.execute(select(DiveCenter)).scalars().first()
    if not dive_center:
        return None
    return {
        "name": dive_center.name,
        "description": dive_center.description or "",
        "phone": dive_center.phone,
        "email": dive_center.email,
        "location": dive_center.location,
        "hotel_name": dive_center.hotel_name or "",
        "coordinates": dive_center.coordinates or {},
        "working_hours": dive_center.working_hours or {},
        "images": dive_center.images or [],
    }


def get_website_settings(db: Session) -> Optional[dict]:
    settings = db.execute(select(WebsiteSettings)).scalars().first()
    if not settings:
        return None
    return {
        "website_title": settings.website_title,
        "default_currency": settings.default_currency or "EGP",
        "contact_phone": settings.contact_phone or "",
        "contact_whatsapp": settings.contact_whatsapp or "",
        "contact_email": settings.contact_email or "",
        "social_links": settings.social_links or {},
    }


# =============================================================================
# User Tools
# =============================================================================


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
            "buyer_name": inv.buyer_name,
            "buyer_email": inv.buyer_email,
            "buyer_phone": inv.buyer_phone,
            "invoice_type": inv.invoice_type,
            "payment_method": inv.payment_method,
            "is_confirmed": inv.is_confirmed,
            "coupon_code": inv.coupon_code,
            "discount_amount": inv.discount_amount,
        }
        for inv in invoices
    ]


def get_user_subscribed_courses(db: Session, user_id: int) -> list[dict]:
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalars().first()
    if not user:
        return []
    return [
        {
            "id": c.id,
            "name": c.name,
            "level": c.course_level,
            "course_type": c.course_type,
            "provider": c.provider,
        }
        for c in (user.subscribed_courses or [])
    ]


# =============================================================================
# Content & Info Tools
# =============================================================================


def get_blog_posts(db: Session, limit: int = 5, tag: Optional[str] = None) -> list[dict]:
    stmt = select(Blog).order_by(Blog.created_at.desc()).limit(limit)
    if tag:
        stmt = select(Blog).where(Blog.tags.any(tag)).order_by(Blog.created_at.desc()).limit(limit)
    blogs = db.execute(stmt).scalars().all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "subject": b.subject,
            "featured_image": b.featured_image or "",
            "tags": b.tags or [],
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in blogs
    ]


def get_testimonials(db: Session, limit: int = 10) -> list[dict]:
    stmt = (
        select(Testimonial)
        .where(Testimonial.is_accepted.is_(True))
        .order_by(Testimonial.created_at.desc())
        .limit(limit)
    )
    testimonials = db.execute(stmt).scalars().all()
    return [
        {
            "id": t.id,
            "description": t.description or "",
            "rating": t.rating,
            "user_name": t.user.full_name if t.user else "Anonymous",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in testimonials
    ]


def get_public_notifications(db: Session, limit: int = 5) -> list[dict]:
    stmt = (
        select(PublicNotification)
        .order_by(PublicNotification.created_at.desc())
        .limit(limit)
    )
    notifications = db.execute(stmt).scalars().all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message or "",
            "type": n.type or "info",
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


# =============================================================================
# Availability Tools
# =============================================================================


def check_activity_availability(
    db: Session,
    activity_type: str,
    activity_id: int,
    check_date: str,
) -> dict:
    try:
        parsed_date = date.fromisoformat(check_date)
    except (ValueError, TypeError):
        return {"available": True, "error": "Invalid date format. Use YYYY-MM-DD."}
    stmt = select(ActivityAvailability).where(
        ActivityAvailability.activity_type == activity_type,
        ActivityAvailability.activity_id == activity_id,
        ActivityAvailability.date == parsed_date,
    )
    closure = db.execute(stmt).scalars().first()
    if closure:
        return {
            "available": False,
            "reason": closure.reason or "Closed on this date",
            "date": check_date,
        }
    return {
        "available": True,
        "date": check_date,
    }


# =============================================================================
# Coupon Tools
# =============================================================================


def get_active_coupons(db: Session, activity: Optional[str] = None) -> list[dict]:
    stmt = select(Coupon).where(Coupon.is_active.is_(True))
    if activity:
        stmt = stmt.where(Coupon.activity == activity)
    coupons = db.execute(stmt).scalars().all()
    now = datetime.utcnow()
    return [
        {
            "id": c.id,
            "code": c.code,
            "activity": c.activity,
            "discount_percentage": c.discount_percentage,
            "remaining": c.remaining,
            "user_limit": c.user_limit,
            "is_expired": c.expire_date is not None and c.expire_date < now,
            "expire_date": c.expire_date.isoformat() if c.expire_date else None,
        }
        for c in coupons
        if c.can_used
    ]


# =============================================================================
# Course Content Tools
# =============================================================================


def get_course_contents(db: Session, course_id: int) -> list[dict]:
    stmt = (
        select(CourseContent)
        .where(CourseContent.course_id == course_id)
        .order_by(CourseContent.order)
    )
    contents = db.execute(stmt).scalars().all()
    return [
        {
            "id": cc.id,
            "title": cc.title,
            "description": (cc.description or "")[:300],
            "content_type": cc.content_type,
            "order": cc.order,
        }
        for cc in contents
    ]


# =============================================================================
# Gallery Tools
# =============================================================================


def get_gallery_images(db: Session, limit: int = 20) -> list[dict]:
    stmt = select(Gallery).order_by(Gallery.created_at.desc()).limit(limit)
    images = db.execute(stmt).scalars().all()
    return [
        {
            "id": img.id,
            "name": img.name,
            "url": img.url,
            "created_at": img.created_at.isoformat() if img.created_at else None,
        }
        for img in images
    ]


# =============================================================================
# Notification Tools (user-specific, requires auth)
# =============================================================================


def get_user_notifications(db: Session, user_id: int, limit: int = 20) -> list[dict]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    notifications = db.execute(stmt).scalars().all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message or "",
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


# =============================================================================
# Comprehensive Best Sellers
# =============================================================================


def get_best_selling_items(db: Session, limit: int = 5) -> dict:
    trips = get_best_selling_trips(db, limit)
    courses = get_best_selling_courses(db, limit)
    return {
        "best_selling_trips": trips,
        "best_selling_courses": courses,
    }


# =============================================================================
# Universal Search (across all products)
# =============================================================================


def search_all_products(
    db: Session,
    query: str = "",
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    limit: int = 5,
) -> dict:
    trips = search_trips(db, query=query, price_min=price_min, price_max=price_max, limit=limit)
    courses = search_courses(db, query=query, limit=limit)
    packages = get_packages(db)
    if query:
        q = query.lower()
        packages = [p for p in packages if q in p["name"].lower() or q in p["description"].lower()]
    return {
        "trips": trips,
        "courses": courses,
        "packages": packages[:limit],
    }


# =============================================================================
# Dashboard / Counts
# =============================================================================


def get_dashboard_data(db: Session) -> dict:
    trips_count = db.execute(select(Trip)).scalars().all()
    courses_count = db.execute(select(Course)).scalars().all()
    packages_count = db.execute(select(Package)).scalars().all()
    testimonials = db.execute(
        select(Testimonial).where(Testimonial.is_accepted.is_(True))
    ).scalars().all()
    return {
        "total_trips": len(trips_count),
        "total_courses": len(courses_count),
        "total_packages": len(packages_count),
        "total_testimonials": len(testimonials),
    }


# =============================================================================
# Converters
# =============================================================================


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


def _course_to_dict(course: Course) -> dict:
    return {
        "id": course.id,
        "name": course.name,
        "description": (course.description or "")[:500],
        "price": course.price if course.price_available else None,
        "level": course.course_level,
        "duration": course.course_duration,
        "duration_unit": course.course_duration_unit or "hours",
        "course_type": course.course_type,
        "provider": course.provider,
        "has_certificate": course.has_certificate,
        "certificate_type": course.certificate_type or "",
        "has_discount": course.has_discount,
        "discount_percentage": course.discount_percentage,
    }


def _package_to_dict(package: Package) -> dict:
    return {
        "id": package.id,
        "name": package.name,
        "description": (package.description or "")[:500],
        "trip_count": len(package.trips) if package.trips else 0,
        "images": package.images or [],
    }
