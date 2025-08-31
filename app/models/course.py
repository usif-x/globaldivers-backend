# app/models/course.py
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Boolean, DateTime, Float, Integer, String, text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base


class Course(Base):
    __tablename__ = "courses"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Course information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    price_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
    price: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0")
    )

    # Course media and settings
    images: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    is_image_list: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'0'")
    )

    # Course details
    course_level: Mapped[str] = mapped_column(String(100), nullable=False)
    course_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    course_duration_unit: Mapped[str] = mapped_column(String(20), nullable=True)
    course_type: Mapped[str] = mapped_column(String(100), nullable=False)
    has_discount: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    discount_requires_min_people: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    discount_always_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    discount_min_people: Mapped[int] = mapped_column(Integer, nullable=True)
    discount_percentage: Mapped[int] = mapped_column(Integer, nullable=True)

    # Certificate settings
    has_certificate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'1'")
    )
    certificate_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Provider and content settings
    provider: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("'Padi'")
    )
    has_online_content: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'1'")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    # Many-to-Many relationship with User
    subscribers: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_course_subscriptions",
        back_populates="subscribed_courses",
        lazy="select",
    )

    # One-to-Many relationship with CourseContent (if you have this model)
    contents: Mapped[List["CourseContent"]] = relationship(
        "CourseContent",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name='{self.name}', price={self.price})>"
