from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.dependencies import get_current_admin
from app.utils.upload_img import (
    delete_uploaded_image,
    get_uploaded_image_path,
    upload_images,
    upload_single_image,
)

upload_routes = APIRouter(prefix="/upload", tags=["Upload Endpoints"])


@upload_routes.post("/image")
async def upload_image_endpoint(
    file: UploadFile = File(...),
    # admin: dict = Depends(get_current_admin)  # Uncomment to require admin auth
):
    """
    Upload a single image file.
    Returns the unique filename.
    """
    try:
        filename = await upload_single_image(file)
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": f"/images/{filename}",
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@upload_routes.post("/images")
async def upload_images_endpoint(
    files: List[UploadFile] = File(...),
    # admin: dict = Depends(get_current_admin)  # Uncomment to require admin auth
):
    """
    Upload multiple image files.
    Returns list of unique filenames.
    """
    try:
        filenames = await upload_images(files)
        return {
            "success": True,
            "message": f"Successfully uploaded {len(filenames)} images",
            "filenames": filenames,
            "urls": [f"/images/{filename}" for filename in filenames],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@upload_routes.delete("/image/{filename}")
async def delete_image_endpoint(
    filename: str,
    admin: dict = Depends(get_current_admin),  # Require admin auth for deletion
):
    """
    Delete an uploaded image.
    Admin only.
    """
    success = delete_uploaded_image(filename)
    if success:
        return {
            "success": True,
            "message": f"Image {filename} deleted successfully",
        }
    else:
        raise HTTPException(status_code=404, detail="Image not found")


@upload_routes.get("/image/{filename}")
async def get_image_endpoint(filename: str):
    """
    Serve an uploaded image file.
    Public endpoint.
    """
    file_path = get_uploaded_image_path(filename)
    if file_path and file_path.exists():
        return FileResponse(path=file_path, media_type="image/*", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Image not found")
