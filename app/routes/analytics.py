from fastapi import APIRouter, Depends, Path
from app.services.analytics import AnalyticsServices
from app.schemas.user import *
from app.core.dependencies import get_db
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_admin
from app.models.user import User






analytics_routes = APIRouter(
  prefix="/analytics",
  tags=["Analytics Endpoints"],
  # dependencies=[Depends(get_current_admin)]
)




@analytics_routes.get("/all")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_all()

@analytics_routes.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_users_count()



@analytics_routes.get("/active-users")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_active_users_count()

@analytics_routes.get("/inactive-users")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_inactive_users_count()



@analytics_routes.get("/blocked-users")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_blocked_users_count()


@analytics_routes.get("/unblocked-users")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_unblocked_users_count()



@analytics_routes.get("/trips")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_trips_count()


@analytics_routes.get("/packages")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_packages_count()


@analytics_routes.get("/testimonials")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_testimonials_count 



@analytics_routes.get("/accepted-testimonials")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_accepted_testimonials_count()



@analytics_routes.get("/unaccepted-testimonials")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_unaccepted_testimonials_count()




@analytics_routes.get("/courses")
async def get_all_users(db: Session = Depends(get_db)):
    return AnalyticsServices(db).get_courses_count


