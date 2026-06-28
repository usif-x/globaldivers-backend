from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transfer import TransferZone
from app.schemas.transfer import TransferZoneBase


class TransferZoneService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[TransferZone]:
        return self.db.execute(select(TransferZone)).scalars().all()

    def get_by_id(self, zone_id: int) -> TransferZone:
        zone = (
            self.db.execute(select(TransferZone).where(TransferZone.id == zone_id))
            .scalars()
            .first()
        )
        if not zone:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Transfer zone not found"
            )
        return zone

    def create(self, data: TransferZoneBase) -> TransferZone:
        existing = (
            self.db.execute(select(TransferZone).where(TransferZone.name == data.name))
            .scalars()
            .first()
        )
        if existing:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="A zone with this name already exists",
            )
        zone = TransferZone(**data.model_dump())
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def update(self, zone_id: int, data: TransferZoneBase) -> TransferZone:
        zone = self.get_by_id(zone_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(zone, field, value)
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def delete(self, zone_id: int):
        zone = self.get_by_id(zone_id)
        self.db.delete(zone)
        self.db.commit()
        return {"success": True, "message": "Transfer zone deleted"}
