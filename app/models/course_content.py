from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text

from app.db.conn import Base

if TYPE_CHECKING:
    from app.models.course import Course


class CourseContent(Base):
    __tablename__ = "course_contents"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., video, pdf, quiz
    content_url: Mapped[str] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
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

    # Relationship to Course
    course: Mapped["Course"] = relationship("Course", back_populates="contents")
