from app.db.conn import Base, engine
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey
from datetime import datetime, timezone




class Gallery(Base):
  __tablename__ = "galleries"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(100), nullable=False)
  images: Mapped[list["Image"]] = relationship(back_populates="gallery")
  description: Mapped[str] = mapped_column(String(500), nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc))
  updated_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))




class Image(Base):
  __tablename__ = "images"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(100), nullable=False)
  url: Mapped[str] = mapped_column(String(100), nullable=False)
  gallery: Mapped[list["Gallery"]] = relationship(back_populates="images")
  gallery_id: Mapped[int] = mapped_column(ForeignKey("galleries.id"), nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc))
  updated_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))






Base.metadata.create_all(bind=engine)