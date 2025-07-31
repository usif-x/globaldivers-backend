from datetime import datetime
from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GalleryResponse(BaseModel):
    id: int
    name: str
    images: list[ImageResponse]
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateGallery(BaseModel):
    name: str
    description: Optional[str]


class UpdateGallery(BaseModel):
    name: Optional[str]
    description: Optional[str]


class CreateImage(BaseModel):
    name: str
    file: UploadFile

    class Config:
        arbitrary_types_allowed = True
