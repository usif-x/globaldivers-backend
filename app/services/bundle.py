from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.bundle import TripBundleOffer
from app.models.invoice import Invoice
from app.models.trip import Trip
from app.schemas.bundle import CreateTripBundleOffer, UpdateTripBundleOffer


class BundleServices:
    def __init__(self, db: Session):
        self.db = db

    def _resolve_trips(self, ids: list):
        return self.db.execute(select(Trip).where(Trip.id.in_(ids))).scalars().all()

    @db_exception_handler
    def create_bundle(self, data: CreateTripBundleOffer):
        payload = data.model_dump()
        required_ids = payload.pop("required_trip_ids")
        bundle = TripBundleOffer(**payload)
        bundle.required_trips = self._resolve_trips(required_ids)
        self.db.add(bundle)
        self.db.commit()
        self.db.refresh(bundle)
        return bundle

    @db_exception_handler
    def get_all_bundles(self):
        return self.db.execute(select(TripBundleOffer)).scalars().all()

    @db_exception_handler
    def get_bundle(self, id: int):
        bundle = self.db.get(TripBundleOffer, id)
        if not bundle:
            raise HTTPException(404, detail="Bundle offer not found")
        return bundle

    @db_exception_handler
    def update_bundle(self, id: int, data: UpdateTripBundleOffer):
        bundle = self.db.get(TripBundleOffer, id)
        if not bundle:
            raise HTTPException(404, detail="Bundle offer not found")
        update_data = data.model_dump(exclude_unset=True)
        required_ids = update_data.pop("required_trip_ids", None)
        for field, value in update_data.items():
            setattr(bundle, field, value)
        if required_ids is not None:
            bundle.required_trips = self._resolve_trips(required_ids)
        self.db.commit()
        self.db.refresh(bundle)
        return bundle

    @db_exception_handler
    def delete_bundle(self, id: int):
        bundle = self.db.get(TripBundleOffer, id)
        if not bundle:
            raise HTTPException(404, detail="Bundle offer not found")
        self.db.delete(bundle)
        self.db.commit()
        return {"success": True, "message": "Bundle offer deleted"}

    @db_exception_handler
    def get_unlocked_offer_for_trip(self, db, user_id: int, trip_id: int):
        """
        Called when a user is booking `trip_id`. Checks whether this trip is the
        `offer_trip` of any active bundle, and whether the user has already booked
        (PAID or PENDING, not cancelled) enough of that bundle's required trips.

        Returns the matching TripBundleOffer, or None.
        """
        now = datetime.now(timezone.utc)

        offers = (
            db.execute(
                select(TripBundleOffer).where(
                    TripBundleOffer.offer_trip_id == trip_id,
                    TripBundleOffer.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )

        if not offers:
            return None

        # trip_ids the user has already booked (adjust status filter to your invoice statuses)
        booked_trip_ids = set(
            db.execute(
                select(
                    Invoice.activity_details
                ).where(  # or a dedicated trip_id column if you have one
                    Invoice.user_id == user_id,
                    Invoice.activity == "trip",
                    Invoice.status.in_(["PAID", "PENDING"]),
                )
            )
            .scalars()
            .all()
        )
        # NOTE: if trip_id isn't a direct column on Invoice, extract it from
        # activity_details JSON instead — see note below.

        for offer in offers:
            if offer.valid_from and now < offer.valid_from:
                continue
            if offer.valid_until and now > offer.valid_until:
                continue

            required_ids = {t.id for t in offer.required_trips}
            matched = required_ids & booked_trip_ids
            needed = offer.min_required_trips or len(required_ids)

            if len(matched) >= needed:
                return offer

        return None
