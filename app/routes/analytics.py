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


# --- NEW: Invoice Analytics Endpoints ---


@analytics_routes.get("/invoices/revenue")
async def get_invoice_revenue(db: Session = Depends(get_db)):
    """Get total invoice revenue (paid invoices only)"""
    from sqlalchemy import func
    from app.models.invoice import Invoice
    
    total_revenue = db.query(func.sum(Invoice.amount)).filter(
        Invoice.status == "PAID"
    ).scalar() or 0.0
    
    return {
        "total_revenue": round(total_revenue, 2),
        "currency": "USD"  # Adjust based on your currency
    }


@analytics_routes.get("/invoices/confirmed")
async def get_confirmed_invoices_stats(db: Session = Depends(get_db)):
    """Get confirmed vs unconfirmed invoice statistics"""
    from app.models.invoice import Invoice
    
    confirmed = db.query(Invoice).filter(Invoice.is_confirmed == True).count()
    unconfirmed = db.query(Invoice).filter(Invoice.is_confirmed == False).count()
    total = confirmed + unconfirmed
    
    return {
        "confirmed_count": confirmed,
        "unconfirmed_count": unconfirmed,
        "total_count": total,
        "confirmation_rate": round((confirmed / total * 100), 2) if total > 0 else 0.0
    }


@analytics_routes.get("/invoices/pickup")
async def get_pickup_stats(db: Session = Depends(get_db)):
    """Get pickup statistics for invoices"""
    from app.models.invoice import Invoice
    
    picked_up = db.query(Invoice).filter(Invoice.picked_up == True).count()
    not_picked_up = db.query(Invoice).filter(Invoice.picked_up == False).count()
    total = picked_up + not_picked_up
    
    return {
        "picked_up_count": picked_up,
        "not_picked_up_count": not_picked_up,
        "total_count": total,
        "pickup_rate": round((picked_up / total * 100), 2) if total > 0 else 0.0
    }

