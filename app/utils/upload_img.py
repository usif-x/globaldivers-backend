import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from PIL import Image


class ImageUploader:
    def __init__(self, upload_dir: str = "storage/images"):
        """
        Initialize the image uploader.

        Args:
            upload_dir: Directory to store uploaded images
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Allowed image extensions
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

        # Maximum file size (10MB)
        self.max_file_size = 10 * 1024 * 1024

    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename with UUID.

        Args:
            original_filename: Original filename from upload

        Returns:
            Unique filename with extension
        """
        # Get file extension
        file_extension = Path(original_filename).suffix.lower()

        # Validate extension
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}",
            )

        # Generate unique ID and combine with extension
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"

    def _validate_image(self, file_path: Path) -> bool:
        """
        Validate that the uploaded file is actually an image.

        Args:
            file_path: Path to the uploaded file

        Returns:
            True if valid image, raises exception otherwise
        """
        try:
            with Image.open(file_path) as img:
                # Verify it's a valid image by trying to load it
                img.verify()
            return True
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid image file or corrupted image"
            )

    async def upload_image(self, file: UploadFile) -> str:
        """
        Upload an image file and return the unique filename.

        Args:
            file: FastAPI UploadFile object

        Returns:
            Unique filename of the uploaded image
        """
        # Check if file is provided
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB",
            )

        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = self.upload_dir / unique_filename

        try:
            # Save the file
            contents = await file.read()

            # Check content size if not provided in file.size
            if len(contents) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB",
                )

            with open(file_path, "wb") as f:
                f.write(contents)

            # Validate the uploaded image
            self._validate_image(file_path)

            return unique_filename

        except HTTPException:
            # Remove file if validation failed
            if file_path.exists():
                file_path.unlink()
            raise
        except Exception as e:
            # Remove file if saving failed
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500, detail=f"Failed to upload image: {str(e)}"
            )

    async def upload_multiple_images(self, files: list[UploadFile]) -> list[str]:
        """
        Upload multiple images and return list of unique filenames.

        Args:
            files: List of FastAPI UploadFile objects

        Returns:
            List of unique filenames
        """
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        uploaded_files = []

        try:
            for file in files:
                filename = await self.upload_image(file)
                uploaded_files.append(filename)

            return uploaded_files

        except Exception:
            # Clean up any successfully uploaded files if one fails
            for filename in uploaded_files:
                file_path = self.upload_dir / filename
                if file_path.exists():
                    file_path.unlink()
            raise

    def delete_image(self, filename: str) -> bool:
        """
        Delete an uploaded image.

        Args:
            filename: Name of the file to delete

        Returns:
            True if deleted successfully, False if file not found
        """
        file_path = self.upload_dir / filename

        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_image_path(self, filename: str) -> Optional[Path]:
        """
        Get the full path to an uploaded image.

        Args:
            filename: Name of the file

        Returns:
            Path object if file exists, None otherwise
        """
        file_path = self.upload_dir / filename
        return file_path if file_path.exists() else None

    def get_image_url(self, filename: str, base_url: str = "") -> str:
        """
        Get the URL to access an uploaded image.

        Args:
            filename: Name of the file
            base_url: Base URL of the application

        Returns:
            Full URL to the image
        """
        return f"{base_url.rstrip('/')}/storage/images/{filename}"


# Create a global instance
image_uploader = ImageUploader()


# Convenience functions
async def upload_single_image(file: UploadFile) -> str:
    """Upload a single image and return the unique filename."""
    return await image_uploader.upload_image(file)


async def upload_images(files: list[UploadFile]) -> list[str]:
    """Upload multiple images and return list of unique filenames."""
    return await image_uploader.upload_multiple_images(files)


def delete_uploaded_image(filename: str) -> bool:
    """Delete an uploaded image."""
    return image_uploader.delete_image(filename)


def get_uploaded_image_path(filename: str) -> Optional[Path]:
    """Get path to an uploaded image."""
    return image_uploader.get_image_path(filename)


def get_image_url(filename: str, base_url: str = "") -> str:
    """Get URL to access an uploaded image."""
    return image_uploader.get_image_url(filename, base_url)
