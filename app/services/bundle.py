from datetime import datetime, timezone

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
        from app.models.invoice import Invoice  # adjust import path if different

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

        # Pull the user's past trip invoices, then extract trip_id from
        # activity_details JSON in Python (no real trip_id column exists yet).
        invoices = (
            db.execute(
                select(Invoice.activity_details).where(
                    Invoice.user_id == user_id,
                    Invoice.activity == "trip",
                    Invoice.status.in_(["PAID", "PENDING"]),
                )
            )
            .scalars()
            .all()
        )

        booked_trip_ids = set()
        for details in invoices:
            if not details:
                continue
            # activity_details is a list of dicts (one per activity_detail entry);
            # trip_id itself isn't stored per-detail — it's on invoice_data.trip_id
            # at creation time, so this only works if you add trip_id to the
            # invoice record or to each activity_details entry. See note below.
            for entry in details:
                tid = entry.get("trip_id")
                if tid is not None:
                    booked_trip_ids.add(tid)

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
