from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ImageBase(BaseModel):
    """Base schema for image"""

    name: str
    url: str


class ImageCreate(ImageBase):
    """Schema for creating image"""

    pass


class ImageUpdate(BaseModel):
    """Schema for updating image"""

    name: Optional[str] = None


class ImageResponse(ImageBase):
    """Schema for image response"""

    id: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    """Schema for paginated image list response"""

    images: list[ImageResponse]
    total: int
    skip: int
    limit: int
