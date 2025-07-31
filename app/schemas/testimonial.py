from datetime import datetime

from pydantic import BaseModel


class CreateTestimonial(BaseModel):
    description: str
    rating: float


class TestimonialResponse(BaseModel):
    id: int
    user_id: int
    description: str
    rating: float
    is_accepted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
