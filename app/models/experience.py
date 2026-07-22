import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    media: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="experience_media_type"), nullable=False
    )
    # Raw S3 object key — resolved to a public URL in ExperienceResponse.
    source: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
