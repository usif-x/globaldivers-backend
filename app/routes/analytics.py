from fastapi import APIRouter, Depends, Path
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_db
from app.models.user import User
from app.schemas.user import *
from app.services.analytics import AnalyticsServices

analytics_routes = APIRouter(
    prefix="/analytics",
    tags=["Analytics Endpoints"],
    # dependencies=[Depends(get_current_admin)]
)


@analytics_routes.get("/all")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_all()


@analytics_routes.get("/users")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_users_count()


@analytics_routes.get("/active-users")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_active_users_count()


@analytics_routes.get("/inactive-users")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_inactive_users_count()


@analytics_routes.get("/blocked-users")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_blocked_users_count()


@analytics_routes.get("/unblocked-users")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_unblocked_users_count()


@analytics_routes.get("/trips")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_trips_count()


@analytics_routes.get("/packages")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_packages_count()


@analytics_routes.get("/testimonials")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_testimonials_count


@analytics_routes.get("/accepted-testimonials")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_accepted_testimonials_count()


@analytics_routes.get("/unaccepted-testimonials")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_unaccepted_testimonials_count()


@analytics_routes.get("/courses")
@cache(expire=600)
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_courses_count
