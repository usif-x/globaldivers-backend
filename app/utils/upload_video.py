"""
Video upload utilities -- thin wrapper around the centralized S3 storage.
"""

from fastapi import UploadFile

from app.utils.storage import upload_video


async def upload_single_video(file: UploadFile) -> str:
    """Upload a single video to S3 and return its object key."""
    return await upload_video(file)
