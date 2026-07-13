from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.bundle import DiscountType


class TripBundleOfferBase(BaseModel):
    name: str
    description: Optional[str] = None
    offer_trip_id: int
    discount_type: DiscountType
    discount_value: float = 0
    required_trip_ids: List[int]
    min_required_trips: int = 0
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class CreateTripBundleOffer(TripBundleOfferBase):
    pass


class UpdateTripBundleOffer(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    offer_trip_id: Optional[int] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    required_trip_ids: Optional[List[int]] = None
    min_required_trips: Optional[int] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class TripBundleOfferResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    offer_trip_id: int
    discount_type: DiscountType
    discount_value: float
    required_trip_ids: List[int] = []
    min_required_trips: int
    is_active: bool
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicableOffersRequest(BaseModel):
    """Sent from checkout with the trip_ids in the cart."""

    trip_ids: List[int]


class ApplicableOfferResult(BaseModel):
    bundle_id: int
    name: str
    offer_trip_id: int
    discount_type: DiscountType
    discount_value: float
    matched_trip_ids: List[int]  # which of the cart's trips satisfied the requirement
