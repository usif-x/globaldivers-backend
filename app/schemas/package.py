from pydantic import BaseModel
from typing import List, Optional


class CreatePackage(BaseModel):
  name: str
  description: str
  images: List[str]
  is_image_list: bool



class PackageResponse(BaseModel):
  id: int
  name: str
  description: str
  images: List[str]
  is_image_list: bool

  class Config:
    from_attributes = True



class UpdatePackage(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  images: Optional[List[str]] = None
  is_image_list: Optional[bool]