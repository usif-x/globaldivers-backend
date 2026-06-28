from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import FeeAppliesTo, FeeType


class TripTransferFeeBase(BaseModel):
    zone_id: int
    fee_type: FeeType = FeeType.fixed
    price: float
    applies_to: FeeAppliesTo = FeeAppliesTo.per_person


class TripTransferFeeResponse(TripTransferFeeBase):
    id: int
    zone_name: Optional[str] = None

    class Config:
        from_attributes = True


class TransferZoneBase(BaseModel):
    name: str
    region: Optional[str] = None


class TransferZoneResponse(TransferZoneBase):
    id: int

    class Config:
        from_attributes = True
