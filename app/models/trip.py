from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .package import Package


class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False)
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
    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id"),
        nullable=False,
    )
    package: Mapped["Package"] = relationship(
        back_populates="trips", passive_deletes=True
    )
    included: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_unit: Mapped[str] = mapped_column(String(20), nullable=True)
    not_included: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    terms_and_conditions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
