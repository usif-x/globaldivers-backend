from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.associations import trip_bundle_requirements


class DiscountType(str, PyEnum):
    percentage = "percentage"
    fixed = "fixed"
    free = "free"


class TripBundleOffer(Base):
    __tablename__ = "trip_bundle_offers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)

    # the trip that becomes discounted/free when the offer is unlocked
    offer_trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    offer_trip = relationship("Trip", foreign_keys=[offer_trip_id])

    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type"), nullable=False
    )
    # percentage -> 0-100, fixed -> currency amount, free -> ignored
    discount_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # trips required to trigger this offer
    required_trips = relationship(
        "Trip", secondary=trip_bundle_requirements, back_populates="bundle_offers"
    )
    # 0 (or null) = ALL required_trips must be booked together.
    # N>0 = ANY N of the required_trips are enough to trigger the offer.
    min_required_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(), nullable=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
