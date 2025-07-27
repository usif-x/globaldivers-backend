from app.services.divesites import DiveSiteService
from fastapi import APIRouter


divesites_routes = APIRouter(
  prefix="/divesites",
  tags=["DiveSite Endpoints"]
)

divesites_routes.get("/")(DiveSiteService().get_dive_sites)

