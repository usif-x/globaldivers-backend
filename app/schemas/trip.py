from typing import List, Optional

from pydantic import BaseModel

from app.schemas.fee import TripFeeBase, TripFeeResponse
from app.schemas.transfer import TripTransferFeeBase, TripTransferFeeResponse


class CreateTrip(BaseModel):
    name: str
    description: str
    images: List[str]
    videos: List[str] = []
    is_image_list: bool = False
    adult_price: float
    child_allowed: bool
    child_price: float
    maxim_person: int
    has_discount: bool
    discount_requires_min_people: bool
    discount_always_available: bool
    discount_min_people: int
    discount_percentage: float
    duration: int
    duration_unit: str
    package_id: int
    included: List[str]
    not_included: List[str]
    terms_and_conditions: List[str]

    # new
    fees: List[TripFeeBase] = []
    transfer_fees: List[TripTransferFeeBase] = []


class TripResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    images: List[str]
    videos: Optional[List[str]] = None
    is_image_list: bool = False
    adult_price: float
    child_allowed: bool
    child_price: float
    maxim_person: int
    package_id: int
    has_discount: bool = False
    discount_requires_min_people: bool = False
    discount_always_available: bool = False
    discount_percentage: Optional[int] = None
    discount_min_people: Optional[int] = None
    included: Optional[List[str]] = None
    duration: Optional[int] = None
    duration_unit: Optional[str]
    not_included: Optional[List[str]] = None
    terms_and_conditions: Optional[List[str]]

    # new
    fees: List[TripFeeResponse] = []
    transfer_fees: List[TripTransferFeeResponse] = []

    class Config:
        from_attributes = True


class UpdateTrip(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    is_image_list: Optional[bool] = None
    adult_price: Optional[float] = None
    child_allowed: Optional[bool] = None
    child_price: Optional[float] = None
    maxim_person: Optional[int] = None
    has_discount: Optional[bool] = None
    discount_requires_min_people: Optional[bool] = None
    discount_always_available: Optional[bool] = None
    discount_percentage: Optional[int] = None
    discount_min_people: Optional[int] = None
    duration: Optional[int] = None
    duration_unit: Optional[str]
    package_id: Optional[int] = None
    included: Optional[List[str]] = None
    not_included: Optional[List[str]] = None
    terms_and_conditions: Optional[List[str]] = None

    # new
    fees: Optional[List[TripFeeBase]] = None
    transfer_fees: Optional[List[TripTransferFeeBase]] = None
