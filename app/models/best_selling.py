from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .course import Course
    from .trip import Trip

import enum


class ItemType(enum.Enum):
    COURSE = "course"
    TRIP = "trip"


class BestSelling(Base):
    __tablename__ = "best_selling"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ranking_position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optional: Add foreign key relationships
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship(
        "Course", foreign_keys=[course_id], passive_deletes=True
    )
    trip: Mapped["Trip"] = relationship(
        "Trip", foreign_keys=[trip_id], passive_deletes=True
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
