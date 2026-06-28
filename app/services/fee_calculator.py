from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fee import TripFee
from app.models.transfer import TripTransferFee


class FeeCalculator:
    """
    Calculates mandatory + optional fees and transfer fees for a trip booking.
    Does NOT touch base price or discounts — that stays in PriceCalculator.
    """

    @staticmethod
    def _fee_amount(fee, adults: int, children: int, base_price: float) -> float:
        people = adults + children

        if fee.applies_to.value == "per_booking":
            units = 1
        elif fee.applies_to.value == "per_adult":
            units = adults
        elif fee.applies_to.value == "per_child":
            units = children
        else:  # per_person
            units = people

        if fee.fee_type.value == "fixed":
            return round(fee.value * units, 2)

        # percentage fees are calculated against the base price, not multiplied
        # by units again — e.g. "5% service fee" means 5% of the booking total,
        # regardless of how many people are on it.
        return round(base_price * (fee.value / 100), 2)

    @staticmethod
    def calculate_addons(
        db: Session,
        trip_id: int,
        adults: int,
        children: int,
        base_price: float,
        transfer_zone_id: Optional[int] = None,
        selected_optional_fee_ids: Optional[list] = None,
    ) -> tuple[float, dict]:
        """
        Returns (addon_total, breakdown_dict).
        addon_total should be ADDED to the discounted base price before verification.
        """
        selected_optional_fee_ids = set(selected_optional_fee_ids or [])

        fees = (
            db.execute(select(TripFee).where(TripFee.trip_id == trip_id))
            .scalars()
            .all()
        )

        mandatory_total = 0.0
        optional_total = 0.0
        mandatory_lines = []
        optional_lines = []

        for fee in fees:
            # Already baked into adult_price — show it for transparency, charge nothing extra.
            if fee.is_included_in_price:
                continue

            amount = FeeCalculator._fee_amount(fee, adults, children, base_price)

            if fee.is_optional:
                if fee.id in selected_optional_fee_ids:
                    optional_total += amount
                    optional_lines.append({"name": fee.name, "amount": amount})
                # not selected -> skip entirely, no charge
            else:
                mandatory_total += amount
                mandatory_lines.append({"name": fee.name, "amount": amount})

        # Validate that selected optional fee ids actually belong to this trip
        valid_optional_ids = {f.id for f in fees if f.is_optional}
        invalid_ids = selected_optional_fee_ids - valid_optional_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid optional fee id(s) for this trip: {sorted(invalid_ids)}",
            )

        transfer_amount = 0.0
        transfer_line = None
        if transfer_zone_id is not None:
            transfer_fee = (
                db.execute(
                    select(TripTransferFee).where(
                        TripTransferFee.trip_id == trip_id,
                        TripTransferFee.zone_id == transfer_zone_id,
                    )
                )
                .scalars()
                .first()
            )

            if not transfer_fee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No transfer pricing configured for this trip and zone",
                )

            transfer_amount = FeeCalculator._fee_amount(
                transfer_fee, adults, children, base_price
            )
            transfer_line = {"zone_id": transfer_zone_id, "amount": transfer_amount}

        addon_total = round(mandatory_total + optional_total + transfer_amount, 2)

        breakdown = {
            "base_price": round(base_price, 2),
            "mandatory_fees": mandatory_lines,
            "mandatory_fees_total": round(mandatory_total, 2),
            "optional_fees": optional_lines,
            "optional_fees_total": round(optional_total, 2),
            "transfer_fee": transfer_line,
            "transfer_fee_total": round(transfer_amount, 2),
            "addon_total": addon_total,
            "final_price": round(base_price + addon_total, 2),
        }

        return addon_total, breakdown
