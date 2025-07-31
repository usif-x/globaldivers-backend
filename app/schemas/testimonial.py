from typing import List, Optional

from pydantic import BaseModel


class CreateTestimonial(BaseModel):
    testimonial_owner: str
    description: str
    rating: float
    is_accepted: Optional[bool] = False


class TestimonialResponse(BaseModel):
    id: int
    user_id: str
    user: List
    description: str
    rating: float
    is_accepted: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
