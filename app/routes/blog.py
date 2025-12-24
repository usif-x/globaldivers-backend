# app/routes/blog.py
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.blog import BlogCreate, BlogListResponse, BlogResponse, BlogUpdate
from app.services.blog import BlogService

blog_routes = APIRouter(prefix="/blogs", tags=["Blog Endpoints"])


# Public endpoints (accessible to everyone)
@blog_routes.get("/", response_model=List[BlogListResponse])
@cache(expire=600)
async def get_all_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get all blog posts (without full text for performance)"""
    return BlogService(db).get_all_blogs(skip=skip, limit=limit)


@blog_routes.get("/id/{blog_id}", response_model=BlogResponse)
@cache(expire=600)
async def get_blog_by_id(blog_id: int, db: Session = Depends(get_db)):
    """Get a blog post by ID"""
    return BlogService(db).get_blog_by_id(blog_id)


@blog_routes.get("/title/{title}", response_model=BlogResponse)
@cache(expire=600)
async def get_blog_by_title(title: str, db: Session = Depends(get_db)):
    """Get a blog post by title"""
    return BlogService(db).get_blog_by_title(title)


@blog_routes.get("/tag/{tag}", response_model=List[BlogListResponse])
@cache(expire=600)
async def get_blogs_by_tag(
    tag: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get all blog posts with a specific tag"""
    return BlogService(db).get_blogs_by_tag(tag, skip=skip, limit=limit)


@blog_routes.get("/search/", response_model=List[BlogListResponse])
@cache(expire=600)
async def search_blogs(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search blogs by title, subject, or content"""
    return BlogService(db).search_blogs(q, skip=skip, limit=limit)


@blog_routes.get("/tags/all", response_model=List[str])
@cache(expire=600)
async def get_all_tags(db: Session = Depends(get_db)):
    """Get all unique tags from all blogs"""
    return BlogService(db).get_all_tags()


# Admin-only endpoints
@blog_routes.post("/upload-image", dependencies=[Depends(get_current_admin)])
async def upload_blog_image(
    image: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload an image for blog content (Admin only)"""
    image_url = await BlogService(db).upload_blog_image(image)
    return {"url": image_url, "filename": image.filename}


@blog_routes.post(
    "/", response_model=BlogResponse, dependencies=[Depends(get_current_admin)]
)
async def create_blog(blog_data: BlogCreate, db: Session = Depends(get_db)):
    """Create a new blog post (Admin only)"""
    return BlogService(db).create_blog(blog_data)


@blog_routes.put(
    "/{blog_id}", response_model=BlogResponse, dependencies=[Depends(get_current_admin)]
)
async def update_blog(
    blog_id: int, blog_data: BlogUpdate, db: Session = Depends(get_db)
):
    """Update a blog post (Admin only)"""
    return BlogService(db).update_blog(blog_id, blog_data)


@blog_routes.delete("/{blog_id}", dependencies=[Depends(get_current_admin)])
async def delete_blog(blog_id: int, db: Session = Depends(get_db)):
    """Delete a blog post (Admin only)"""
    return BlogService(db).delete_blog(blog_id)
