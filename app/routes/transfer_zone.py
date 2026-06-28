from typing import List

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.transfer import TransferZoneBase, TransferZoneResponse
from app.services.transfer_zone import TransferZoneService

transfer_zone_routes = APIRouter(
    prefix="/transfer-zones", tags=["Transfer Zone Endpoints"]
)


@transfer_zone_routes.get("/", response_model=List[TransferZoneResponse])
async def get_all_zones(db: Session = Depends(get_db)):
    return await run_in_threadpool(TransferZoneService(db).get_all)


@transfer_zone_routes.post(
    "/", response_model=TransferZoneResponse, dependencies=[Depends(get_current_admin)]
)
async def create_zone(data: TransferZoneBase, db: Session = Depends(get_db)):
    return await run_in_threadpool(TransferZoneService(db).create, data)


@transfer_zone_routes.put(
    "/{zone_id}",
    response_model=TransferZoneResponse,
    dependencies=[Depends(get_current_admin)],
)
async def update_zone(
    zone_id: int, data: TransferZoneBase, db: Session = Depends(get_db)
):
    return await run_in_threadpool(TransferZoneService(db).update, zone_id, data)


@transfer_zone_routes.delete("/{zone_id}", dependencies=[Depends(get_current_admin)])
async def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    return await run_in_threadpool(TransferZoneService(db).delete, zone_id)
