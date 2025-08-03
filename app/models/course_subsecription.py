from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey

from app.db.conn import Base


class UserCourseSubscription(Base):
    __tablename__ = "user_course_subscriptions"
    user_id: int = Column(ForeignKey("users.id"), primary_key=True)
    course_id: int = Column(ForeignKey("courses.id"), primary_key=True)

    subscribed_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
