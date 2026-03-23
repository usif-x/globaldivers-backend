from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.package import Package
from app.schemas.package import CreatePackage, PackageResponse, UpdatePackage
from app.utils.storage import delete_file, get_public_url
from app.utils.upload_img import upload_images


class PackageServices:

    def __init__(self, db: Session):
        self.db = db

    def _convert_keys_to_urls(self, keys: List[str]) -> List[str]:
        """Convert S3 object keys to full public URLs."""
        if not keys:
            return []
        return [get_public_url(key) for key in keys]

    @db_exception_handler
    async def create_package(
        self, package: CreatePackage, images: List[UploadFile] = None
    ):
        image_keys = []
        if images:
            try:
                image_keys = await upload_images(images)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload images: {str(e)}"
                )

        package_data = package.model_dump()
        package_data["images"] = image_keys

        new_package = Package(**package_data)
        self.db.add(new_package)
        self.db.commit()
        self.db.refresh(new_package)

        new_package.images = self._convert_keys_to_urls(new_package.images)
        return new_package

    @db_exception_handler
    def get_all_packages(self):
        stmt = select(Package)
        packages = self.db.execute(stmt).scalars().all()

        for package in packages:
            package.images = self._convert_keys_to_urls(package.images)

        return packages

    @db_exception_handler
    def get_package_by_id(self, id: int):
        stmt = select(Package).where(Package.id == id)
        package = self.db.execute(stmt).scalars().first()
        if package:
            package.images = self._convert_keys_to_urls(package.images)
            return package
        else:
            raise HTTPException(404, detail="Package not found")

    @db_exception_handler
    def delete_package(self, id: int):
        try:
            stmt = select(Package).where(Package.id == id)
            package = self.db.execute(stmt).scalars().first()
            if package:
                if package.images:
                    for key in package.images:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete image {key}: {e}")

                self.db.delete(package)
                self.db.commit()
                return {"success": True, "message": "Package deleted successfully"}
            else:
                raise HTTPException(404, detail="Package not found")
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting package: {str(e)}"}

    @db_exception_handler
    async def update_package(
        self, package: UpdatePackage, id: int, images: List[UploadFile] = None
    ):
        stmt = select(Package).where(Package.id == id)
        updated_package = self.db.execute(stmt).scalars().first()
        if updated_package:
            if images:
                try:
                    if updated_package.images:
                        for old_key in updated_package.images:
                            try:
                                delete_file(old_key)
                            except Exception as e:
                                print(f"Failed to delete old image {old_key}: {e}")

                    new_image_keys = await upload_images(images)

                    data = package.model_dump(exclude_unset=True)
                    data["images"] = new_image_keys

                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Failed to upload new images: {str(e)}"
                    )
            else:
                data = package.model_dump(exclude_unset=True)

            for field, value in data.items():
                setattr(updated_package, field, value)

            self.db.commit()
            self.db.refresh(updated_package)

            updated_package.images = self._convert_keys_to_urls(
                updated_package.images
            )

            return {
                "success": True,
                "message": "Package Updated successfully",
                "package": PackageResponse.model_validate(
                    updated_package, from_attributes=True
                ),
            }
        else:
            raise HTTPException(404, detail="Package not found")

    @db_exception_handler
    def get_trip_by_package_id(self, id: int):
        stmt = select(Package).where(Package.id == id)
        package = self.db.execute(stmt).scalars().first()
        if package:
            package.images = self._convert_keys_to_urls(package.images)
            return package.trips
        else:
            raise HTTPException(404, detail="Package not found")

    @db_exception_handler
    def delete_all_packages(self):
        try:
            packages = self.db.execute(select(Package)).scalars().all()

            for package in packages:
                if package.images:
                    for key in package.images:
                        try:
                            delete_file(key)
                        except Exception as e:
                            print(f"Failed to delete image {key}: {e}")

            self.db.execute(delete(Package))
            self.db.commit()
            return {"success": True, "message": "All packages deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting packages: {str(e)}"}
