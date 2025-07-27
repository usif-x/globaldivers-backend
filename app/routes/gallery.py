from fastapi import APIRouter, Depends, Path
from app.services.gallery import GalleryServices
from app.schemas.gallery import  CreateGallery, CreateImage, GalleryResponse, ImageResponse, UpdateGallery, UpdateImage
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_admin




gallery_routes = APIRouter(
  prefix="/galleries",
  tags=["Gallery Endpoints"],
  dependencies=[Depends(get_current_admin)]
)



@gallery_routes.post("/", response_model=GalleryResponse)
async def create_gallery(gallery: CreateGallery, db: Session = Depends(get_db)):
    return GalleryServices(db).create_gallery(gallery)


@gallery_routes.get("/", response_model=list[GalleryResponse])
async def get_all_galleries(db: Session = Depends(get_db)):
    return GalleryServices(db).get_all_galleries()


@gallery_routes.get("/{id}", response_model=GalleryResponse)
async def get_gallery_by_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return GalleryServices(db).get_gallery_by_id(id)



@gallery_routes.put("/{id}", response_model=GalleryResponse)
async def update_gallery(gallery: UpdateGallery, id: int, db: Session = Depends(get_db)):
    return GalleryServices(db).update_gallery(gallery, id)


@gallery_routes.delete("/{id}", response_model=dict)
async def delete_gallery(id: int, db: Session = Depends(get_db)):
    return GalleryServices(db).delete_gallery(id)




@gallery_routes.post("/{id}/images", response_model=ImageResponse)
async def create_image(image: CreateImage, id: int, db: Session = Depends(get_db)):
    return GalleryServices(db).create_image(image, id)


@gallery_routes.put("images/{image_id}", response_model=ImageResponse)
async def update_image(image: UpdateImage, image_id: int, db: Session = Depends(get_db)):
    return GalleryServices(db).update_image(image, image_id)



@gallery_routes.delete("images/{image_id}", response_model=dict)
async def delete_image(id: int, image_id: int, db: Session = Depends(get_db)):
    return GalleryServices(db).delete_image(image_id)



@gallery_routes.get("all-images", response_model=list[ImageResponse])
async def get_all_images(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return GalleryServices(db).get_all_images(id)

@gallery_routes.get("images/{image_id}", response_model=ImageResponse)
async def get_image_by_id(image_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    return GalleryServices(db).get_image_by_id(image_id)

