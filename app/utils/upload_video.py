import os
from pathlib import Path

from fastapi import HTTPException, UploadFile


class VideoUploader:
    def __init__(self, upload_dir: str = None):
        if upload_dir is None:
            base_storage = os.getenv("STORAGE_PATH", "storage")
            upload_dir = os.path.join(base_storage, "videos")
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        self.max_file_size = 100 * 1024 * 1024  # 100MB

    async def upload_video(self, file: UploadFile) -> str:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}",
            )
        contents = await file.read()
        if len(contents) > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB",
            )
        unique_filename = f"{os.urandom(16).hex()}{file_extension}"
        file_path = self.upload_dir / unique_filename
        try:
            with open(file_path, "wb") as f:
                f.write(contents)
            return unique_filename
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500, detail=f"Failed to upload video: {str(e)}"
            )


video_uploader = VideoUploader()


async def upload_single_video(file: UploadFile) -> str:
    return await video_uploader.upload_video(file)
