from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.package import Package
from app.schemas.package import CreatePackage, PackageResponse, UpdatePackage


class PackageServices:

    def __init__(self, db: Session):
        self.db = db

    def create_package(self, package: CreatePackage):
        new_package = Package(**package.model_dump())
        self.db.add(new_package)
        self.db.commit()
        self.db.refresh(new_package)
        return new_package

    def get_all_packages(self):
        stmt = select(Package)
        packages = self.db.execute(stmt).scalars().all()
        return packages

    def get_package_by_id(self, id: int):
        stmt = select(Package).where(Package.id == id)
        package = self.db.execute(stmt).scalars().first()
        return package

    def delete_package(self, id: int):
        stmt = select(Package).where(Package.id == id)
        package = self.db.execute(stmt).scalars().first()
        if package:
            self.db.delete(package)
            self.db.commit()
            return {"success": True, "message": "Package deleted successfully"}
        else:
            raise HTTPException(404, detail="Package not found")

    def update_package(self, package: UpdatePackage, id: int):
        stmt = select(Package).where(Package.id == id)
        updated_package = self.db.execute(stmt).scalars().first()
        if updated_package:
            data = package.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(updated_package, field, value)
            self.db.commit()
            self.db.refresh(updated_package)
            return {
                "success": True,
                "message": "Package Updated successfuly",
                "package": PackageResponse.model_validate(
                    updated_package, from_attributes=True
                ),
            }
        else:
            raise HTTPException(404, detail="Package not found")

    def delete_all_packages(self):
        stmt = select(Package)
        packages = self.db.execute(stmt).scalars().all()
        for package in packages:
            self.db.delete(package)
        self.db.commit()
        return {"success": True, "message": "All packages deleted successfully"}

    def get_trip_by_package_id(self, id: int):
        stmt = select(Package).where(Package.id == id)
        package = self.db.execute(stmt).scalars().first()
        if package:
            return package.trips
        else:
            raise HTTPException(404, detail="Package not found")
