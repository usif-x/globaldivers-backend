# app/models/activity_availability.py

from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActivityAvailability(Base):
    """
    Tracks when activities (trips/courses) are CLOSED.
    If a record exists for a date → activity is CLOSED
    If no record exists → activity is OPEN (default)
    """

    __tablename__ = "activity_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'trip' or 'course'
    activity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Ensure one activity can only be closed once per date
    __table_args__ = (
        UniqueConstraint(
            "activity_type", "activity_id", "date", name="uq_activity_date"
        ),
    )

    def __repr__(self) -> str:
        return f"<ActivityAvailability(activity_type={self.activity_type}, activity_id={self.activity_id}, date={self.date})>"
