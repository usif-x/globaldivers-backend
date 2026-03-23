from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dive_center import DiveCenter
from app.schemas.dive_center import DiveCenterCreate, DiveCenterUpdate
from app.utils.storage import get_public_url
from app.utils.upload_img import upload_images
from app.utils.upload_video import upload_single_video


class DiveCenterService:
    def __init__(self, db: Session):
        self.db = db

    async def create_dive_center(
        self,
        data: DiveCenterCreate,
        image_files: list[UploadFile] = None,
        video_file: UploadFile = None,
    ) -> DiveCenter:
        # Upload images if provided
        images = []
        if image_files:
            images = await upload_images(image_files)

        # Upload video if provided
        video = None
        if video_file:
            video = await upload_single_video(video_file)

        center_data = data.model_dump()
        if images:
            center_data["images"] = images
            center_data["is_image_list"] = True
        if video:
            center_data["video"] = video

        new_center = DiveCenter(**center_data)
        self.db.add(new_center)
        self.db.commit()
        self.db.refresh(new_center)
        return new_center

    def get_dive_center_by_id(self, dive_center_id: int) -> DiveCenter:
        stmt = select(DiveCenter).where(DiveCenter.id == dive_center_id)
        result = self.db.execute(stmt).scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="Dive center not found")
        return result

    def get_all_dive_centers(self) -> list[DiveCenter]:
        stmt = select(DiveCenter).order_by(DiveCenter.created_at.desc())
        result = self.db.execute(stmt).scalars().all()
        return result

    def update_dive_center(
        self, dive_center_id: int, data: DiveCenterUpdate
    ) -> DiveCenter:
        center = self.get_dive_center_by_id(dive_center_id)
        for key, value in data.dict(exclude_unset=True).items():
            setattr(center, key, value)
        self.db.commit()
        self.db.refresh(center)
        return center

    def delete_dive_center(self, dive_center_id: int) -> None:
        center = self.get_dive_center_by_id(dive_center_id)
        self.db.delete(center)
        self.db.commit()
