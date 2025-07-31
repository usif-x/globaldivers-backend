from fastapi import APIRouter

from app.services.divesites import DiveSiteService

divesites_routes = APIRouter(prefix="/divesites", tags=["DiveSite Endpoints"])

divesites_routes.get("/")(DiveSiteService().get_dive_sites)
