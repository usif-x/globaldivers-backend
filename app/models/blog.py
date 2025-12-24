# app/models/blog.py
from datetime import datetime, timezone
from typing import List

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Blog(Base):
    """Blog model for storing blog posts with structured content blocks"""

    __tablename__ = "blogs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Blog information
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)

    # Featured/main image (displayed with title and subject)
    featured_image: Mapped[str] = mapped_column(String(500), nullable=True)

    # Content blocks: [{"type": "text", "content": "..."}, {"type": "image", "url": "...", "alt": "..."}]
    content: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)

    # Tags/topics
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Blog(id={self.id}, title='{self.title}')>"
