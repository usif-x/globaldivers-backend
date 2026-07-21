from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dive_center import DiveCenter
from app.schemas.dive_center import DiveCenterCreate, DiveCenterUpdate
from app.utils.upload_img import upload_images
from app.utils.upload_video import upload_single_video


def _clean_files(files: list[UploadFile] | None) -> list[UploadFile]:
    """Drop empty file parts (filename == '') that browsers append when no file is picked."""
    if not files:
        return []
    return [f for f in files if f and f.filename]


class DiveCenterService:
    def __init__(self, db: Session):
        self.db = db

    async def create_dive_center(
        self,
        data: DiveCenterCreate,
        image_files: list[UploadFile] = None,
        video_file: UploadFile = None,
    ) -> DiveCenter:
        image_files = _clean_files(image_files)
        video_file = video_file if (video_file and video_file.filename) else None

        images = []
        if image_files:
            try:
                images = await upload_images(image_files)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

        video = None
        if video_file:
            try:
                video = await upload_single_video(video_file)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Video upload failed: {e}")

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
        return self.db.execute(stmt).scalars().all()

    async def update_dive_center(
        self,
        dive_center_id: int,
        data: DiveCenterUpdate,
        image_files: list[UploadFile] = None,
        video_file: UploadFile = None,
        replace_images: bool = False,
    ) -> DiveCenter:
        center = self.get_dive_center_by_id(dive_center_id)

        image_files = _clean_files(image_files)
        video_file = video_file if (video_file and video_file.filename) else None

        if image_files:
            try:
                new_images = await upload_images(image_files)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
            center.images = (
                new_images if replace_images else list(center.images or []) + new_images
            )
            center.is_image_list = True

        if video_file:
            try:
                center.video = await upload_single_video(video_file)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Video upload failed: {e}")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(center, key, value)

        self.db.commit()
        self.db.refresh(center)
        return center

    def delete_dive_center(self, dive_center_id: int) -> None:
        center = self.get_dive_center_by_id(dive_center_id)
        self.db.delete(center)
        self.db.commit()
