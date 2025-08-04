from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.setting import WebsiteSettingsResponse, WebsiteSettingsUpdate
from app.services.setting import WebsiteSettingsService

setting_routes = APIRouter(
    prefix="/settings",
    tags=["Settings Endpoints"],
)


@setting_routes.get("/", response_model=WebsiteSettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    return WebsiteSettingsService(db).get_settings()


@setting_routes.put(
    "/",
    dependencies=[Depends(get_current_admin)],
    response_model=WebsiteSettingsResponse,
)
async def update_settings(
    settings: WebsiteSettingsUpdate, db: Session = Depends(get_db)
):
    return WebsiteSettingsService(db).update_settings(settings)
