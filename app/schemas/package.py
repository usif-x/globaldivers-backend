from typing import List, Optional

from fastapi import UploadFile
from pydantic import BaseModel


class CreatePackage(BaseModel):
    name: str
    description: str
    is_image_list: bool = True


class CreatePackageWithImages(BaseModel):
    name: str
    description: str
    is_image_list: bool = True


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
    is_image_list: Optional[bool] = None
