from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table

from app.core.database import Base

user_course_subscriptions = Table(
    "user_course_subscriptions",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "course_id",
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "subscribed_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
    extend_existing=True,
)

coupon_user_usage = Table(
    "coupon_user_usage",
    Base.metadata,
    Column(
        "coupon_id",
        Integer,
        ForeignKey("coupons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "used_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
    Column("usage_count", Integer, default=1, nullable=False),
    extend_existing=True,
)

# --- Trip-related associations (NEW) -----------------------------------

trip_packages = Table(
    "trip_packages",
    Base.metadata,
    Column(
        "trip_id", Integer, ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "package_id",
        Integer,
        ForeignKey("packages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
    extend_existing=True,
)

# Self-referential, kept symmetric in the service layer (if A relates to B,
# service inserts both (A,B) and (B,A) rows so either side can query it directly).
trip_relations = Table(
    "trip_relations",
    Base.metadata,
    Column(
        "trip_id", Integer, ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "related_trip_id",
        Integer,
        ForeignKey("trips.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
    extend_existing=True,
)

trip_bundle_requirements = Table(
    "trip_bundle_requirements",
    Base.metadata,
    Column(
        "bundle_id",
        Integer,
        ForeignKey("trip_bundle_offers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "trip_id", Integer, ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True
    ),
    extend_existing=True,
)
