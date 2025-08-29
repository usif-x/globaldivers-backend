from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base

from .package import Package


class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_image_list: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    egp_adult_price: Mapped[float] = mapped_column(Float, nullable=False)
    egp_child_price: Mapped[float] = mapped_column(Float, nullable=False)
    usd_adult_price: Mapped[float] = mapped_column(Float, nullable=False)
    usd_child_price: Mapped[float] = mapped_column(Float, nullable=False)
    eur_adult_price: Mapped[float] = mapped_column(Float, nullable=False)
    eur_child_price: Mapped[float] = mapped_column(Float, nullable=False)
    maxim_person: Mapped[int] = mapped_column(Integer, nullable=False)
    has_discount: Mapped[bool] = mapped_column(
        Boolean, nullable=True, server_default=text("0")
    )
    discount_percentage: Mapped[int] = mapped_column(Integer, nullable=True)
    duration: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("8")
    )
    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id"),
        nullable=False,
    )
    package: Mapped["Package"] = relationship(
        back_populates="trips", passive_deletes=True
    )
    included: Mapped[list[str]] = mapped_column(JSON, nullable=False)
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
