from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception_handler import db_exception_handler
from app.models.package import Package
from app.schemas.package import CreatePackage, PackageResponse, UpdatePackage
from app.utils.upload_img import delete_uploaded_image, upload_images


class PackageServices:

    def __init__(self, db: Session):
        self.db = db

    def _convert_filenames_to_urls(self, filenames: List[str]) -> List[str]:
        """Convert image filenames to full URLs"""
        if not filenames:
            return []

        base_url = settings.APP_URL.rstrip("/")
        return [f"{base_url}/storage/images/{filename}" for filename in filenames]

    def _extract_filenames_from_urls(self, urls: List[str]) -> List[str]:
        """Extract filenames from full URLs (for delete operations)"""
        if not urls:
            return []

        filenames = []
        for url in urls:
            if "/storage/images/" in url:
                filename = url.split("/storage/images/")[-1]
                filenames.append(filename)
        return filenames

    @db_exception_handler
    async def create_package(
        self, package: CreatePackage, images: List[UploadFile] = None
    ):
        # Upload images if provided
        image_filenames = []
        if images:
            try:
                # Upload all images and get their filenames
                image_filenames = await upload_images(images)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to upload images: {str(e)}"
                )

        # Create package with uploaded image filenames
        package_data = package.model_dump()
        package_data["images"] = image_filenames

        new_package = Package(**package_data)
        self.db.add(new_package)
        self.db.commit()
        self.db.refresh(new_package)

        # Convert filenames to full URLs before returning
        new_package.images = self._convert_filenames_to_urls(new_package.images)
        return new_package

    @db_exception_handler
    def get_all_packages(self):
        stmt = select(Package)
        packages = self.db.execute(stmt).scalars().all()

        # Convert filenames to full URLs for all packages
        for package in packages:
            package.images = self._convert_filenames_to_urls(package.images)

        return packages

    @db_exception_handler
    def get_package_by_id(self, id: int):
        stmt = select(Package).where(Package.id == id)
        package = self.db.execute(stmt).scalars().first()
        if package:
            # Convert filenames to full URLs
            package.images = self._convert_filenames_to_urls(package.images)
            return package
        else:
            raise HTTPException(404, detail="Package not found")

    @db_exception_handler
    def delete_package(self, id: int):
        try:
            stmt = select(Package).where(Package.id == id)
            package = self.db.execute(stmt).scalars().first()
            if package:
                # Delete associated images from storage
                if package.images:
                    # Extract filenames from URLs if needed
                    filenames_to_delete = (
                        self._extract_filenames_from_urls(package.images)
                        if package.images
                        and "/storage/images/"
                        in (package.images[0] if package.images else "")
                        else package.images
                    )

                    for image_filename in filenames_to_delete:
                        try:
                            delete_uploaded_image(image_filename)
                        except Exception as e:
                            print(f"Failed to delete image {image_filename}: {e}")

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
            # Handle image updates
            if images:
                try:
                    # Delete old images from storage
                    if updated_package.images:
                        # Extract filenames from URLs if needed
                        old_filenames = (
                            self._extract_filenames_from_urls(updated_package.images)
                            if updated_package.images
                            and "/storage/images/"
                            in (
                                updated_package.images[0]
                                if updated_package.images
                                else ""
                            )
                            else updated_package.images
                        )

                        for old_image in old_filenames:
                            try:
                                delete_uploaded_image(old_image)
                            except Exception as e:
                                print(f"Failed to delete old image {old_image}: {e}")

                    # Upload new images
                    new_image_filenames = await upload_images(images)

                    # Update package data
                    data = package.model_dump(exclude_unset=True)
                    data["images"] = new_image_filenames

                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Failed to upload new images: {str(e)}"
                    )
            else:
                # No new images, just update other fields
                data = package.model_dump(exclude_unset=True)

            # Apply updates
            for field, value in data.items():
                setattr(updated_package, field, value)

            self.db.commit()
            self.db.refresh(updated_package)

            # Convert filenames to full URLs before returning
            updated_package.images = self._convert_filenames_to_urls(
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
            # Convert filenames to full URLs for the package
            package.images = self._convert_filenames_to_urls(package.images)
            return package.trips
        else:
            raise HTTPException(404, detail="Package not found")

    @db_exception_handler
    def delete_all_packages(self):
        try:
            # Get all packages to delete their images
            packages = self.db.execute(select(Package)).scalars().all()

            # Delete all associated images from storage
            for package in packages:
                if package.images:
                    # Extract filenames from URLs if needed
                    filenames_to_delete = (
                        self._extract_filenames_from_urls(package.images)
                        if package.images
                        and "/storage/images/"
                        in (package.images[0] if package.images else "")
                        else package.images
                    )

                    for image_filename in filenames_to_delete:
                        try:
                            delete_uploaded_image(image_filename)
                        except Exception as e:
                            print(f"Failed to delete image {image_filename}: {e}")

            # Delete all packages from database
            self.db.execute(delete(Package))
            self.db.commit()
            return {"success": True, "message": "All packages deleted successfully"}
        except SQLAlchemyError as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting packages: {str(e)}"}
