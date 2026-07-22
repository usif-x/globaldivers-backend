from datetime import datetime
from enum import Enum

from pydantic import BaseModel, model_validator

from app.utils.storage import get_public_url


class MediaType(str, Enum):
    image = "image"
    video = "video"


class ExperienceResponse(BaseModel):
    id: int
    media: MediaType
    source: str
    created_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _resolve_url(self):
        # DB stores a raw S3 key; convert to a usable public URL on the way out.
        self.source = get_public_url(self.source)
        return self
