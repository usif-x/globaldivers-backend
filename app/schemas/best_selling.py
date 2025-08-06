from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field

from app.models.best_selling import ItemType
from app.schemas.course import CourseResponse
from app.schemas.trip import TripResponse


class BestSellingBase(BaseModel):
    item_type: ItemType
    item_id: int = Field(..., gt=0, description="ID of the course or trip")
    ranking_position: int = Field(
        ..., gt=0, description="Position in best selling ranking"
    )


class BestSellingCreate(BestSellingBase):
    pass


class BestSellingUpdate(BaseModel):
    item_type: Optional[ItemType] = None
    item_id: Optional[int] = Field(None, gt=0)
    ranking_position: Optional[int] = Field(None, gt=0)


class BestSellingInDB(BestSellingBase):
    id: int
    course_id: Optional[int] = None
    trip_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BestSellingResponse(BestSellingInDB):
    # You can add related course/trip data here if needed
    course: Optional[CourseResponse] = None
    trip: Optional[TripResponse] = None

    class Config:
        from_attributes = True


class BestSellingListResponse(BaseModel):
    items: list[BestSellingResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
