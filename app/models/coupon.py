# app/models/coupon.py
from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Coupon information
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    activity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'all'")
    )  # trip, course, all

    discount_percentage: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Discount percentage (e.g., 10.5 for 10.5% off)

    # Usage tracking
    can_used_up_to: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    user_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )  # How many times a user can use this coupon (0 = unlimited)
    used_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    # Expiration
    expire_date: Mapped[datetime] = mapped_column(DateTime(), nullable=True)

    # Tracking fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships - Many-to-Many with User
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="coupon_user_usage",
        back_populates="used_coupons",
        lazy="select",
    )

    @property
    def remaining(self) -> int:
        """Calculate remaining coupon usage count"""
        return max(0, self.can_used_up_to - self.used_count)

    @property
    def can_used(self) -> bool:
        """Check if coupon can still be used"""
        if not self.is_active:
            return False
        if self.remaining <= 0:
            return False
        if self.expire_date and datetime.utcnow() > self.expire_date:
            return False
        return True

    def __repr__(self) -> str:
        return f"<Coupon(id={self.id}, code='{self.code}', activity='{self.activity}')>"
