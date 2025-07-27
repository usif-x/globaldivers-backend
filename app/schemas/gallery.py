from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageResponse(BaseModel):
  id: int
  name: str
  url: str
  created_at: datetime
  updated_at: datetime


class GalleryResponse(BaseModel):
  id: int
  name: str
  images: list[ImageResponse]
  description: Optional[str] = None
  created_at: datetime
  updated_at: datetime


class CreateGallery(BaseModel):
  name: str
  description: Optional[str]


class CreateImage(BaseModel):
  name: str
  url: str


class UpdateGallery(BaseModel):
  name: Optional[str]
  description: Optional[str]


class UpdateImage(BaseModel):
  name: Optional[str]
  url: Optional[str]


  