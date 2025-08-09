from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table
from app.db.conn import Base

user_course_subscriptions = Table(
    'user_course_subscriptions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    Column('subscribed_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
    extend_existing=True
)
