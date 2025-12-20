# app/models/user.py
from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User information
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("user")
    )

    # Status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    # Tracking fields
    last_login: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships - One-to-Many
    testimonials: Mapped[List["Testimonial"]] = relationship(
        "Testimonial",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Many-to-Many relationship with Course
    subscribed_courses: Mapped[List["Course"]] = relationship(
        "Course",
        secondary="user_course_subscriptions",
        back_populates="subscribers",
        lazy="select",
    )

    # Many-to-Many relationship with Coupon
    used_coupons: Mapped[List["Coupon"]] = relationship(
        "Coupon", secondary="coupon_user_usage", back_populates="users", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.full_name}', email='{self.email}')>"
