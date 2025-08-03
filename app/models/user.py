from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base

if TYPE_CHECKING:
    from .course import Course
    from .invoice import Invoice
    from .testimonial import Testimonial


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'user'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'1'")
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'0'")
    )
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

    testimonials: Mapped[List["Testimonial"]] = relationship(
        "Testimonial", back_populates="user", cascade="all, delete-orphan"
    )

    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="user", cascade="all, delete-orphan"
    )
    subscribed_courses: Mapped[List["Course"]] = relationship(
        "Course",
        secondary="user_course_subscriptions",  # Use the name of the association table
        back_populates="subscribers",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.full_name})>"
