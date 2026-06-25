"""
Video upload utilities -- thin wrapper around the centralized S3 storage.
"""

import asyncio
from typing import List, Optional

from fastapi import UploadFile

from app.utils.storage import delete_file, get_public_url, upload_video


async def upload_single_video(file: UploadFile) -> str:
    """Upload a single video to S3 and return its object key."""
    return await upload_video(file)


async def upload_videos(files: List[UploadFile]) -> List[str]:
    """Upload multiple videos to S3 and return list of object keys."""
    return list(await asyncio.gather(*(upload_video(f) for f in files)))


def delete_uploaded_video(filename_or_key: str) -> bool:
    """Delete a video from S3. Accepts object key, URL, or bare filename."""
    return delete_file(filename_or_key)


def get_video_url(filename: str) -> Optional[str]:
    """Return the public S3 URL for a video."""
    return get_public_url(filename) if filename else None
