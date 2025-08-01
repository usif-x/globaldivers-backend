from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base

from .user import User


class Testimonial(Base):
    __tablename__ = "testimonials"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user: Mapped["User"] = relationship(back_populates="testimonial")
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    rating: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0")
    )
    is_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    is_rejected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
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
