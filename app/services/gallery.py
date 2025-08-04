import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.gallery import Gallery
from app.schemas.gallery import ImageCreate, ImageUpdate


class ImageService:
    """Service class for handling image operations"""

    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = storage_dir
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        os.makedirs(storage_dir, exist_ok=True)

    def _validate_image_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image"
            )

        file_extension = os.path.splitext(file.filename or "")[1].lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension {file_extension} not allowed. Allowed: {', '.join(self.allowed_extensions)}",
            )

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        return unique_filename

    async def create_image(self, db: Session, file: UploadFile) -> Gallery:
        """Upload image to storage and create database record"""
        # Validate file
        self._validate_image_file(file)

        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename or "image")
        file_path = os.path.join(self.storage_dir, unique_filename)

        try:
            # Save file to storage
            async with aiofiles.open(file_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            # Create database record
            image_url = f"/storage/{unique_filename}"
            db_image = Gallery(name=file.filename or unique_filename, url=image_url)

            db.add(db_image)
            db.commit()
            db.refresh(db_image)

            return db_image

        except Exception as e:
            db.rollback()
            # Clean up file if database operation failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}",
            )

    def get_images(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Gallery], int]:
        """Get all images with pagination and total count"""
        total = db.query(func.count(Gallery.id)).scalar()
        images = (
            db.query(Gallery)
            .order_by(Gallery.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return images, total

    def get_image(self, db: Session, image_id: int) -> Optional[Gallery]:
        """Get specific image by ID"""
        return db.query(Gallery).filter(Gallery.id == image_id).first()

    def update_image(
        self, db: Session, image_id: int, image_update: ImageUpdate
    ) -> Optional[Gallery]:
        """Update image metadata"""
        db_image = db.query(Gallery).filter(Gallery.id == image_id).first()
        if not db_image:
            return None

        try:
            if image_update.name is not None:
                db_image.name = image_update.name

            db.commit()
            db.refresh(db_image)
            return db_image

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update image: {str(e)}",
            )

    def delete_image(self, db: Session, image_id: int) -> bool:
        """Delete image from storage and database"""
        db_image = db.query(Gallery).filter(Gallery.id == image_id).first()
        if not db_image:
            return False

        try:
            # Extract filename from URL
            filename = db_image.url.split("/")[-1]
            file_path = os.path.join(self.storage_dir, filename)

            # Delete from database
            db.delete(db_image)
            db.commit()

            # Delete file from storage
            if os.path.exists(file_path):
                os.remove(file_path)

            return True

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}",
            )

    def delete_all_images(self, db: Session) -> int:
        """Delete all images from storage and database"""
        try:
            # Get all images
            images = db.query(Gallery).all()
            deleted_count = len(images)

            # Delete files from storage
            for image in images:
                filename = image.url.split("/")[-1]
                file_path = os.path.join(self.storage_dir, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Delete all records from database
            db.query(Gallery).delete()
            db.commit()

            return deleted_count

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete all images: {str(e)}",
            )
