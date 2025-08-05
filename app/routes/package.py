from fastapi import APIRouter, Depends, Path
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.package import CreatePackage, PackageResponse, UpdatePackage
from app.schemas.trip import TripResponse
from app.services.package import PackageServices

package_routes = APIRouter(prefix="/packages", tags=["Package Endpoints"])


@package_routes.post(
    "/", response_model=PackageResponse, dependencies=[Depends(get_current_admin)]
)
async def create_package(package: CreatePackage, db: Session = Depends(get_db)):
    return PackageServices(db).create_package(package)


@package_routes.get("/", response_model=list[PackageResponse])
@cache(expire=600)
async def get_all_packages(db: Session = Depends(get_db)):
    return PackageServices(db).get_all_packages()


@package_routes.get("/{id}", response_model=PackageResponse)
async def get_package_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return PackageServices(db).get_package_by_id(id)


@package_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_package(id: int, db: Session = Depends(get_db)):
    return PackageServices(db).delete_package(id)


@package_routes.put("/{id}", dependencies=[Depends(get_current_admin)])
async def update_package(
    package: UpdatePackage, id: int, db: Session = Depends(get_db)
):
    return PackageServices(db).update_package(package, id)


@package_routes.get("/{id}/trips", response_model=list[TripResponse])
@cache(expire=600)
async def get_trip_by_package_id(
    id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    return PackageServices(db).get_trip_by_package_id(id)
