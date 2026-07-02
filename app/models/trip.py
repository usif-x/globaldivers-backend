from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.associations import (
    trip_bundle_requirements,
    trip_packages,
    trip_relations,
)

from .package import Package


class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    videos: Mapped[list[str]] = mapped_column(JSON, nullable=True, default=list)
    is_image_list: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    adult_price: Mapped[float] = mapped_column(Float, nullable=False)
    child_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=True, default=False, server_default=text("false")
    )
    child_price: Mapped[float] = mapped_column(Float, nullable=False)
    maxim_person: Mapped[int] = mapped_column(Integer, nullable=False)
    has_discount: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    discount_requires_min_people: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    discount_always_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    discount_min_people: Mapped[int] = mapped_column(Integer, nullable=True)
    discount_percentage: Mapped[int] = mapped_column(Integer, nullable=True)

    # REMOVED: package_id single FK + package relationship
    # NEW: many-to-many
    packages: Mapped[list["Package"]] = relationship(
        "Package", secondary=trip_packages, back_populates="trips"
    )

    included: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    fees = relationship("TripFee", back_populates="trip", cascade="all, delete-orphan")
    transfer_fees = relationship(
        "TripTransferFee", back_populates="trip", cascade="all, delete-orphan"
    )
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_unit: Mapped[str] = mapped_column(String(20), nullable=True)
    not_included: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    terms_and_conditions: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # NEW: self-referential many-to-many, symmetric (kept symmetric in the service layer)
    related_trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        secondary=trip_relations,
        primaryjoin="Trip.id == trip_relations.c.trip_id",
        secondaryjoin="Trip.id == trip_relations.c.related_trip_id",
    )

    # NEW: bundle offers this trip is a *requirement* for
    bundle_offers: Mapped[list["TripBundleOffer"]] = relationship(
        "TripBundleOffer",
        secondary=trip_bundle_requirements,
        back_populates="required_trips",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
