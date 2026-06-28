from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import FeeAppliesTo, FeeType


class TripFeeBase(BaseModel):
    name: str
    fee_type: FeeType = FeeType.fixed
    value: float
    applies_to: FeeAppliesTo = FeeAppliesTo.per_person
    is_optional: bool = False
    is_included_in_price: bool = False
    description: Optional[str] = None


class TripFeeResponse(TripFeeBase):
    id: int

    class Config:
        from_attributes = True
