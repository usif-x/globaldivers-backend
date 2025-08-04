from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.gallery import ImageListResponse, ImageResponse, ImageUpdate
from app.services.gallery import ImageService

# Create router
gallery_routes = APIRouter(prefix="/gallery", tags=["Gallery"])

# Initialize service
image_service = ImageService()


@gallery_routes.post(
    "/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED
)
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload an image to storage and save metadata to database

    - **file**: Image file to upload (jpg, jpeg, png, gif, bmp, webp)
    """
    image = await image_service.create_image(db, file)
    return image


@gallery_routes.get("/", response_model=ImageListResponse)
def get_all_images(
    skip: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of images to return"),
    db: Session = Depends(get_db),
):
    """
    Get all images from gallery with pagination

    - **skip**: Number of images to skip (default: 0)
    - **limit**: Maximum number of images to return (default: 100, max: 1000)
    """
    images, total = image_service.get_images(db, skip=skip, limit=limit)
    return ImageListResponse(images=images, total=total, skip=skip, limit=limit)


@gallery_routes.get("/{image_id}", response_model=ImageResponse)
def get_image(image_id: int, db: Session = Depends(get_db)):
    """
    Get specific image by ID

    - **image_id**: Unique identifier of the image
    """
    image = image_service.get_image(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )
    return image


@gallery_routes.put("/{image_id}", response_model=ImageResponse)
def update_image(
    image_id: int, image_update: ImageUpdate, db: Session = Depends(get_db)
):
    """
    Update image metadata

    - **image_id**: Unique identifier of the image
    - **image_update**: Updated image data
    """
    image = image_service.update_image(db, image_id, image_update)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )
    return image


@gallery_routes.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: int, db: Session = Depends(get_db)):
    """
    Delete image from storage and database

    - **image_id**: Unique identifier of the image to delete
    """
    success = image_service.delete_image(db, image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )


@gallery_routes.delete("/", status_code=status.HTTP_200_OK)
def delete_all_images(db: Session = Depends(get_db)):
    """
    Delete all images from storage and database

    Returns the number of deleted images
    """
    deleted_count = image_service.delete_all_images(db)
    return {"message": f"Successfully deleted {deleted_count} images"}
