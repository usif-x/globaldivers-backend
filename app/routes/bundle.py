from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.bundle import (
    ApplicableOffersRequest,
    CreateTripBundleOffer,
    TripBundleOfferResponse,
    UpdateTripBundleOffer,
)
from app.services.bundle import BundleServices
from app.services.trip import TripServices

bundle_routes = APIRouter(prefix="/bundles", tags=["Bundle Offers"])


@bundle_routes.get("/", response_model=list[TripBundleOfferResponse])
async def get_all_bundles(db: Session = Depends(get_db)):
    return BundleServices(db).get_all_bundles()


@bundle_routes.post(
    "/",
    response_model=TripBundleOfferResponse,
    dependencies=[Depends(get_current_admin)],
)
async def create_bundle(data: CreateTripBundleOffer, db: Session = Depends(get_db)):
    return BundleServices(db).create_bundle(data)


@bundle_routes.put(
    "/{id}",
    response_model=TripBundleOfferResponse,
    dependencies=[Depends(get_current_admin)],
)
async def update_bundle(
    id: int, data: UpdateTripBundleOffer, db: Session = Depends(get_db)
):
    return BundleServices(db).update_bundle(id, data)


@bundle_routes.delete("/{id}", dependencies=[Depends(get_current_admin)])
async def delete_bundle(id: int, db: Session = Depends(get_db)):
    return BundleServices(db).delete_bundle(id)


@bundle_routes.post("/applicable")
async def get_applicable_offers(
    payload: ApplicableOffersRequest, db: Session = Depends(get_db)
):
    """Called from the cart/checkout page to see which offers just got unlocked."""
    return TripServices(db).get_applicable_offers(payload.trip_ids)


@bundle_routes.get("/unlocked/{trip_id}", dependencies=[Depends(get_current_user)])
async def get_unlocked_offer(
    trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    offer = BundleServices(db).get_unlocked_offer_for_trip(
        db=db, user_id=current_user.id, trip_id=trip_id
    )
    return offer  # None or the offer details, frontend calls this when trip detail page loads
