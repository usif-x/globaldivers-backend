# app/services/blog.py
import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.blog import Blog
from app.schemas.blog import BlogCreate, BlogUpdate


class BlogService:
    """Service class for handling blog operations"""

    def __init__(self, db: Session, storage_dir: str = None):
        self.db = db
        if storage_dir is None:
            storage_dir = os.getenv("STORAGE_PATH", "storage")
        self.storage_dir = os.path.join(storage_dir, "blogs")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

    def _validate_image_file(self, file: UploadFile) -> None:
        """Validate uploaded image file"""
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image"
            )

        file_extension = os.path.splitext(file.filename or "")[1].lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension {file_extension} not allowed. Allowed: {', '.join(self.allowed_extensions)}",
            )

    async def upload_blog_image(self, file: UploadFile) -> str:
        """Upload image for blog and return URL"""
        self._validate_image_file(file)

        # Generate unique filename
        file_extension = os.path.splitext(file.filename or "image")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.storage_dir, unique_filename)

        try:
            # Save file to storage
            async with aiofiles.open(file_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            # Return URL path
            return f"/storage/blogs/{unique_filename}"

        except Exception as e:
            # Clean up file if upload failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}",
            )

    def get_all_blogs(self, skip: int = 0, limit: int = 100) -> List[Blog]:
        """Get all blog posts with pagination"""
        return self.db.query(Blog).offset(skip).limit(limit).all()

    def get_blog_by_id(self, blog_id: int) -> Blog:
        """Get a blog post by ID"""
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blog with ID {blog_id} not found",
            )
        return blog

    def get_blog_by_title(self, title: str) -> Blog:
        """Get a blog post by title"""
        blog = self.db.query(Blog).filter(Blog.title == title).first()
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blog with title '{title}' not found",
            )
        return blog

    def get_blogs_by_tag(self, tag: str, skip: int = 0, limit: int = 100) -> List[Blog]:
        """Get all blog posts with a specific tag"""
        # SQLAlchemy JSON query for MySQL/PostgreSQL
        return (
            self.db.query(Blog)
            .filter(Blog.tags.contains([tag]))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_blogs(
        self, search_query: str, skip: int = 0, limit: int = 100
    ) -> List[Blog]:
        """Search blogs by title, subject, or content"""
        search_pattern = f"%{search_query}%"
        return (
            self.db.query(Blog)
            .filter(
                or_(
                    Blog.title.ilike(search_pattern),
                    Blog.subject.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_blog(self, blog_data: BlogCreate) -> Blog:
        """Create a new blog post"""
        # Check if blog with same title already exists
        existing_blog = (
            self.db.query(Blog).filter(Blog.title == blog_data.title).first()
        )
        if existing_blog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Blog with title '{blog_data.title}' already exists",
            )

        # Convert content blocks to dict format
        content_data = [
            block.model_dump(exclude_none=True) for block in blog_data.content
        ]

        # Create new blog
        db_blog = Blog(
            title=blog_data.title,
            subject=blog_data.subject,
            content=content_data,
            tags=blog_data.tags,
        )

        try:
            self.db.add(db_blog)
            self.db.commit()
            self.db.refresh(db_blog)
            return db_blog
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create blog: {str(e)}",
            )

    def update_blog(self, blog_id: int, blog_data: BlogUpdate) -> Blog:
        """Update an existing blog post"""
        blog = self.get_blog_by_id(blog_id)

        # Check if new title conflicts with existing blog
        if blog_data.title and blog_data.title != blog.title:
            existing_blog = (
                self.db.query(Blog).filter(Blog.title == blog_data.title).first()
            )
            if existing_blog:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Blog with title '{blog_data.title}' already exists",
                )

        # Update fields
        update_data = blog_data.model_dump(exclude_unset=True)

        # Convert content blocks if present
        if "content" in update_data and update_data["content"] is not None:
            update_data["content"] = [
                block.model_dump(exclude_none=True) for block in blog_data.content
            ]

        for field, value in update_data.items():
            setattr(blog, field, value)

        try:
            self.db.commit()
            self.db.refresh(blog)
            return blog
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update blog: {str(e)}",
            )

    def delete_blog(self, blog_id: int) -> dict:
        """Delete a blog post"""
        blog = self.get_blog_by_id(blog_id)

        try:
            self.db.delete(blog)
            self.db.commit()
            return {"message": f"Blog '{blog.title}' deleted successfully"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete blog: {str(e)}",
            )

    def get_all_tags(self) -> List[str]:
        """Get all unique tags from all blogs"""
        blogs = self.db.query(Blog).all()
        all_tags = set()
        for blog in blogs:
            all_tags.update(blog.tags)
        return sorted(list(all_tags))
