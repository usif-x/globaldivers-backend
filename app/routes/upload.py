from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse

from app.core.dependencies import get_current_admin
from app.utils.storage import get_public_url
from app.utils.upload_img import (
    delete_uploaded_image,
    upload_images,
    upload_single_image,
)

upload_routes = APIRouter(prefix="/upload", tags=["Upload Endpoints"])


@upload_routes.post("/image")
async def upload_image_endpoint(
    file: UploadFile = File(...),
):
    """
    Upload a single image file to S3.
    Returns the object key and full URL.
    """
    try:
        object_key = await upload_single_image(file)
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "filename": object_key,
            "url": get_public_url(object_key),
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@upload_routes.post("/images")
async def upload_images_endpoint(
    files: List[UploadFile] = File(...),
):
    """
    Upload multiple image files to S3.
    Returns list of object keys and URLs.
    """
    try:
        keys = await upload_images(files)
        return {
            "success": True,
            "message": f"Successfully uploaded {len(keys)} images",
            "filenames": keys,
            "urls": [get_public_url(k) for k in keys],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@upload_routes.delete("/image/{filename:path}")
async def delete_image_endpoint(
    filename: str,
    admin: dict = Depends(get_current_admin),
):
    """
    Delete an uploaded image from S3.
    Admin only.
    """
    success = delete_uploaded_image(filename)
    if success:
        return {
            "success": True,
            "message": f"Image {filename} deleted successfully",
        }
    else:
        raise HTTPException(status_code=404, detail="Image not found or already deleted")


@upload_routes.get("/image/{filename:path}")
async def get_image_endpoint(filename: str):
    """
    Redirect to the S3 public URL for the image.
    """
    url = get_public_url(filename)
    return RedirectResponse(url=url)
