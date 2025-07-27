from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, String, Float, Boolean, text, ForeignKey
from app.db.conn import Base, engine
from datetime import datetime, timezone
from .user import User




class Testimonial(Base):
  __tablename__ = "testimonials"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  testimonial_owner: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
  user: Mapped["User"] = relationship(back_populates="testimonial")
  description: Mapped[str] = mapped_column(String(500), nullable=True)
  rating: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
  is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
  created_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc))
  updated_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))





Base.metadata.create_all(bind=engine)