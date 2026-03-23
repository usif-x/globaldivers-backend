import logging
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.gallery import Gallery
from app.schemas.gallery import ImageCreate, ImageUpdate
from app.utils.storage import delete_file, get_public_url, upload_image

logger = logging.getLogger(__name__)


class ImageService:
    """Service class for handling gallery image operations via S3."""

    async def create_image(self, db: Session, file: UploadFile) -> Gallery:
        """Upload image to S3 and create database record."""
        try:
            object_key = await upload_image(file, prefix="gallery")
            image_url = get_public_url(object_key)

            db_image = Gallery(
                name=file.filename or object_key,
                url=image_url,
            )
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            return db_image

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}",
            )

    def get_images(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Gallery], int]:
        """Get all images with pagination and total count."""
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
        """Get specific image by ID."""
        return db.query(Gallery).filter(Gallery.id == image_id).first()

    def update_image(
        self, db: Session, image_id: int, image_update: ImageUpdate
    ) -> Optional[Gallery]:
        """Update image metadata."""
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
        """Delete image from S3 and database."""
        db_image = db.query(Gallery).filter(Gallery.id == image_id).first()
        if not db_image:
            return False

        try:
            # Delete from database first
            db.delete(db_image)
            db.commit()

            # Delete from S3
            delete_file(db_image.url)
            return True

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}",
            )

    def delete_all_images(self, db: Session) -> int:
        """Delete all images from S3 and database."""
        try:
            images = db.query(Gallery).all()
            deleted_count = len(images)

            # Delete files from S3
            for image in images:
                try:
                    delete_file(image.url)
                except Exception as e:
                    logger.warning(f"Failed to delete S3 object for {image.url}: {e}")

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
