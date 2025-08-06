from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import HttpUrl, validate_arguments
from sqlalchemy import JSON, Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.conn import Base


class DiveCenter(Base):
    __tablename__ = "dive_centers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(10000), nullable=True)

    # Store image URLs as a JSON list of validated URLs
    images: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    is_image_list: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

    # Location fields
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    hotel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    coordinates: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSON, nullable=True, default=lambda: {"latitude": 0.0, "longitude": 0.0}
    )

    # Working hours with structured start/end times
    working_hours: Mapped[Dict[str, Dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "monday": {"start": "09:00", "end": "17:00", "is_open": True},
            "tuesday": {"start": "09:00", "end": "17:00", "is_open": True},
            "wednesday": {"start": "09:00", "end": "17:00", "is_open": True},
            "thursday": {"start": "09:00", "end": "17:00", "is_open": True},
            "friday": {"start": "09:00", "end": "17:00", "is_open": True},
            "saturday": {"start": "10:00", "end": "14:00", "is_open": True},
            "sunday": {"start": "", "end": "", "is_open": False},
        },
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @validate_arguments
    def add_image(self, url: HttpUrl):
        """Add a validated image URL to the images list."""
        if not self.images:
            self.images = []
        self.images.append(str(url))
        self.is_image_list = True
