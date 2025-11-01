from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Path, UploadFile
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.package import CreatePackage, PackageResponse, UpdatePackage
from app.schemas.trip import TripResponse
from app.services.package import PackageServices

package_routes = APIRouter(prefix="/packages", tags=["Package Endpoints"])


@package_routes.post("/", response_model=PackageResponse)
async def create_package(
    name: str = Form(...),
    description: str = Form(...),
    is_image_list: bool = Form(True),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Create a new package with image uploads.
    """
    package_data = CreatePackage(
        name=name, description=description, is_image_list=is_image_list
    )
    return await PackageServices(db).create_package(package_data, images)


@package_routes.get("/", response_model=list[PackageResponse])
@cache(expire=600)
async def get_all_packages(db: Session = Depends(get_db)):
    return PackageServices(db).get_all_packages()


@package_routes.get("/{id}", response_model=PackageResponse)
async def get_package_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return PackageServices(db).get_package_by_id(id)


@package_routes.delete("/all")
async def delete_all_packages(db: Session = Depends(get_db)):
    return PackageServices(db).delete_all_packages()


@package_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_package(id: int, db: Session = Depends(get_db)):
    return PackageServices(db).delete_package(id)


@package_routes.put("/{id}")
async def update_package(
    id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_image_list: Optional[bool] = Form(None),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Update a package. If images are provided, they will replace existing images.
    """
    package_data = UpdatePackage(
        name=name, description=description, is_image_list=is_image_list
    )
    return await PackageServices(db).update_package(package_data, id, images)


@package_routes.get("/{id}/trips")
@cache(expire=600)
async def get_trip_by_package_id(
    id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    return PackageServices(db).get_trip_by_package_id(id)
