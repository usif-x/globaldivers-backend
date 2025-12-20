from datetime import datetime

from pydantic import BaseModel


class CreateTestimonial(BaseModel):
    description: str
    notes: str | None = None
    rating: float


class TestimonialResponse(BaseModel):
    id: int
    user_id: int
    description: str
    rating: float
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
