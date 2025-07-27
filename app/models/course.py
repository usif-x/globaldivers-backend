from app.db.conn import Base, engine
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, text, Boolean, Integer, DateTime, Float
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import JSON
from app.db.conn import engine


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_image_list: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    course_level: Mapped[str] = mapped_column(String(100), nullable=False)
    course_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))




Base.metadata.create_all(bind=engine)