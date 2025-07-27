from app.models.gallery import Gallery, Image
from app.schemas.gallery import CreateGallery, CreateImage, GalleryResponse, ImageResponse, UpdateGallery
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.exception_handler import db_exception_handler
from app.utils.imgbb import upload_image_to_imgbb






class GalleryServices:
  def __init__(self, db: Session):
    self.db = db


  @db_exception_handler
  def create_gallery(self, gallery: CreateGallery):
    new_gallery = Gallery(**gallery.model_dump())
    self.db.add(new_gallery)
    self.db.commit()
    self.db.refresh(new_gallery)
    return new_gallery
  

  @db_exception_handler
  def get_all_galleries(self):
    stmt = select(Gallery)
    galleries = self.db.execute(stmt).scalars().all()
    return galleries
  

  @db_exception_handler
  def get_gallery_by_id(self, id: int):
    stmt = select(Gallery).where(Gallery.id == id)
    gallery = self.db.execute(stmt).scalars().first()
    return gallery
  



  @db_exception_handler
  def update_gallery(self, gallery: UpdateGallery, id: int):
    stmt = select(Gallery).where(Gallery.id == id)
    updated_gallery = self.db.execute(stmt).scalars().first()
    if updated_gallery:
      data = gallery.model_dump(exclude_unset=True)
      for field, value in data.items():
        setattr(updated_gallery, field, value)
      self.db.commit()
      self.db.refresh(updated_gallery)
      return {"success": True, 
              "message": "Gallery Updated successfuly", 
              "gallery": GalleryResponse.model_validate(updated_gallery,from_attributes=True)}
    else:
      raise HTTPException(404, detail="Gallery not found")
    


  @db_exception_handler
  def delete_gallery(self, id: int):
    stmt = select(Gallery).where(Gallery.id == id)
    gallery = self.db.execute(stmt).scalars().first()
    if gallery:
      self.db.delete(gallery)
      self.db.commit()
      return {"success": True, "message": "Gallery deleted successfully"}
    else:
      raise HTTPException(404, detail="Gallery not found")
    


  @db_exception_handler
  async def create_image(self, image: CreateImage, gallery_id: int):
    file_bytes = await image.file.read()  # ✅ أضف await
    uploaded = upload_image_to_imgbb(file_bytes)
    if "data" in uploaded:
        image_url = uploaded["data"]["url"]
    else:
        raise Exception("Failed to upload image to imgbb")
    new_image = Image(
        name=image.name,
        url=image_url,
        gallery_id=gallery_id
    )

    self.db.add(new_image)
    self.db.commit()
    self.db.refresh(new_image)
    return new_image

  

  @db_exception_handler
  def get_all_images(self):
    stmt = select(Image)
    images = self.db.execute(stmt).scalars().all()
    return images
  
  @db_exception_handler
  def get_image_by_id(self, id: int):
    stmt = select(Image).where(Image.id == id)
    image = self.db.execute(stmt).scalars().first()
    return image
  

  @db_exception_handler
  def delete_image(self, id: int):
    stmt = select(Image).where(Image.id == id)
    image = self.db.execute(stmt).scalars().first()
    if image:
      self.db.delete(image)
      self.db.commit()
      return {"success": True, "message": "Image deleted successfully"}
    else:
      raise HTTPException(404, detail="Image not found")
    


