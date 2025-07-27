from app.db.conn import Base, engine
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import JSON
from app.db.conn import engine
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .trip import Trip



class Package(Base):
    __tablename__ = "packages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_image_list: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    trips: Mapped[List["Trip"]] = relationship(back_populates="package")




Base.metadata.create_all(bind=engine)