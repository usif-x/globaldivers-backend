"""
Image upload utilities -- thin wrappers around the centralized S3 storage.

Existing callers can keep importing from this module without changes.
"""

from typing import Optional

from fastapi import UploadFile

from app.utils.storage import (
    delete_file,
    get_public_url,
    upload_image,
    upload_multiple_images,
)


# ---- Convenience functions (backwards-compatible API) ----

async def upload_single_image(file: UploadFile) -> str:
    """Upload a single image to S3 and return its object key."""
    return await upload_image(file)


async def upload_images(files: list[UploadFile]) -> list[str]:
    """Upload multiple images to S3 and return list of object keys."""
    return await upload_multiple_images(files)


def delete_uploaded_image(filename_or_key: str) -> bool:
    """Delete an image from S3. Accepts object key, URL, or bare filename."""
    return delete_file(filename_or_key)


def get_uploaded_image_path(filename: str) -> Optional[str]:
    """
    Return the public URL for a stored image.

    .. deprecated::
        Prefer ``get_image_url`` or ``storage.get_public_url`` directly.
    """
    # Return the URL string; callers that checked ``.exists()`` should
    # instead rely on the S3 object existing.
    return get_public_url(f"images/{filename}") if filename else None


def get_image_url(filename: str, base_url: str = "") -> str:
    """
    Return the public S3 URL for an image.

    The ``base_url`` parameter is ignored (kept for signature compatibility).
    """
    return get_public_url(filename)
