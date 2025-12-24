# app/schemas/blog.py
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """Schema for a content block (text or image)"""

    type: Literal["text", "image"]
    content: Optional[str] = None  # For text blocks (supports markdown)
    url: Optional[str] = None  # For image blocks
    alt: Optional[str] = None  # Alt text for images
    caption: Optional[str] = None  # Optional caption for images


class BlogCreate(BaseModel):
    """Schema for creating a new blog post"""

    title: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=500)
    featured_image: Optional[str] = Field(None, max_length=500)
    content: List[ContentBlock] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class BlogUpdate(BaseModel):
    """Schema for updating an existing blog post"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    featured_image: Optional[str] = Field(None, max_length=500)
    content: Optional[List[ContentBlock]] = None
    tags: Optional[List[str]] = None


class BlogResponse(BaseModel):
    """Schema for blog post response"""

    id: int
    title: str
    subject: str
    featured_image: Optional[str]
    content: List[dict]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlogListResponse(BaseModel):
    """Schema for blog list response (without full content)"""

    id: int
    title: str
    subject: str
    featured_image: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
