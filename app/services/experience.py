from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experience import Experience, MediaType
from app.utils.upload_img import delete_uploaded_image, upload_single_image
from app.utils.upload_video import delete_uploaded_video, upload_single_video

VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".avi", ".mkv")


def _detect_media_type(file: UploadFile) -> MediaType:
    content_type = (file.content_type or "").lower()
    if content_type.startswith("video/"):
        return MediaType.video
    if content_type.startswith("image/"):
        return MediaType.image

    # Some clients send application/octet-stream — fall back to extension.
    name = (file.filename or "").lower()
    return MediaType.video if name.endswith(VIDEO_EXTENSIONS) else MediaType.image


class ExperienceService:
    def __init__(self, db: Session):
        self.db = db

    async def create_experience(self, file: UploadFile) -> Experience:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="A media file is required.")

        media_type = _detect_media_type(file)

        try:
            source = (
                await upload_single_video(file)
                if media_type == MediaType.video
                else await upload_single_image(file)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

        new_experience = Experience(media=media_type, source=source)
        self.db.add(new_experience)
        self.db.commit()
        self.db.refresh(new_experience)
        return new_experience

    def get_all_experiences(self) -> list[Experience]:
        stmt = select(Experience).order_by(Experience.created_at.desc())
        return self.db.execute(stmt).scalars().all()

    def get_experience_by_id(self, experience_id: int) -> Experience:
        stmt = select(Experience).where(Experience.id == experience_id)
        result = self.db.execute(stmt).scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="Experience not found")
        return result

    def delete_experience(self, experience_id: int) -> None:
        experience = self.get_experience_by_id(experience_id)

        try:
            if experience.media == MediaType.video:
                delete_uploaded_video(experience.source)
            else:
                delete_uploaded_image(experience.source)
        except Exception:
            pass  # DB row should still go even if S3 cleanup fails

        self.db.delete(experience)
        self.db.commit()
