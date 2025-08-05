from datetime import datetime, timezone
from typing import TYPE_CHECKING, List  # Import List

from sqlalchemy import Boolean, DateTime, Float, Integer, String, text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base

if TYPE_CHECKING:
    from .course_content import CourseContent
    from .user import User  # Import User for type hinting


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    price: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0")
    )
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_image_list: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    course_level: Mapped[str] = mapped_column(String(100), nullable=False)
    course_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    course_type: Mapped[str] = mapped_column(String(100), nullable=False)
    has_certificate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
    certificate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("Padi")
    )
    has_online_content: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
    contents: Mapped[List["CourseContent"]] = relationship(
        "CourseContent", back_populates="course", cascade="all, delete"
    )
    subscribers: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_course_subscriptions",
        back_populates="subscribed_courses",
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


from app.models.course_content import CourseContent

Course.contents = relationship(
    "CourseContent", back_populates="course", cascade="all, delete"
)
