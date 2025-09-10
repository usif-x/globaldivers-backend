# app/models/testimonial.py
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Testimonial(Base):
    __tablename__ = "testimonials"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Testimonial data
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    rating: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0")
    )

    # Status fields
    is_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'0'")
    )
    is_rejected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("'0'")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="testimonials",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Testimonial(id={self.id}, user_id={self.user_id}, rating={self.rating})>"
