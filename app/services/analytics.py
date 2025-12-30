from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.invoice import Invoice
from app.models.package import Package
from app.models.testimonial import Testimonial
from app.models.trip import Trip
from app.models.user import User


class AnalyticsServices:
    def __init__(self, db: Session):
        self.db = db

    def get_users_count(self):
        return self.db.query(User).count()

    def get_active_users_count(self):
        return self.db.query(User).filter(User.is_active == True).count()

    def get_inactive_users_count(self):
        return self.db.query(User).filter(User.is_active == False).count()

    def get_blocked_users_count(self):
        return self.db.query(User).filter(User.is_blocked == True).count()

    def get_unblocked_users_count(self):
        return self.db.query(User).filter(User.is_blocked == False).count()

    def get_trips_count(self):
        return self.db.query(Trip).count()

    def get_packages_count(self):
        return self.db.query(Package).count()

    def get_testimonials_count(self):
        return self.db.query(Testimonial).count()

    def get_accepted_testimonials_count(self):
        return (
            self.db.query(Testimonial).filter(Testimonial.is_accepted == True).count()
        )

    def get_unaccepted_testimonials_count(self):
        return (
            self.db.query(Testimonial).filter(Testimonial.is_accepted == False).count()
        )

    def get_courses_count(self):
        return self.db.query(Course).count()

    def get_invoices_count(self):
        return self.db.query(Invoice).count()

    def get_pending_invoices_count(self):
        return self.db.query(Invoice).filter(Invoice.status == "PENDING").count()

    def get_expired_invoices_count(self):
        return self.db.query(Invoice).filter(Invoice.status == "EXPIRED").count()

    def get_paid_invoices_count(self):
        return self.db.query(Invoice).filter(Invoice.status == "PAID").count()

    def get_unpaid_invoices_count(self):
        return self.db.query(Invoice).filter(Invoice.status == "NEW").count()

    def get_cancelled_invoices_count(self):
        return self.db.query(Invoice).filter(Invoice.status == "CANCELLED").count()

    def get_all(self):
        # Invoice revenue metrics
        total_invoice_revenue = (
            self.db.query(func.sum(Invoice.amount))
            .filter(Invoice.status == "PAID")
            .scalar() or 0.0
        )
        pending_invoice_revenue = (
            self.db.query(func.sum(Invoice.amount))
            .filter(Invoice.status == "PENDING")
            .scalar() or 0.0
        )
        
        # Confirmed/unconfirmed invoices
        confirmed_invoices = (
            self.db.query(Invoice).filter(Invoice.is_confirmed == True).count()
        )
        unconfirmed_invoices = (
            self.db.query(Invoice).filter(Invoice.is_confirmed == False).count()
        )
        
        # Pickup tracking
        picked_up_invoices = (
            self.db.query(Invoice).filter(Invoice.picked_up == True).count()
        )
        not_picked_up_invoices = (
            self.db.query(Invoice).filter(Invoice.picked_up == False).count()
        )
        
        return {
            # User metrics
            "users_count": self.get_users_count(),
            "active_users_count": self.get_active_users_count(),
            "inactive_users_count": self.get_inactive_users_count(),
            "blocked_users_count": self.get_blocked_users_count(),
            "unblocked_users_count": self.get_unblocked_users_count(),
            
            # Content metrics
            "trips_count": self.get_trips_count(),
            "packages_count": self.get_packages_count(),
            "courses_count": self.get_courses_count(),
            
            # Testimonial metrics
            "testimonials_count": self.get_testimonials_count(),
            "accepted_testimonials_count": self.get_accepted_testimonials_count(),
            "unaccepted_testimonials_count": self.get_unaccepted_testimonials_count(),
            
            # Invoice count metrics
            "invoices_count": self.get_invoices_count(),
            "pending_invoices_count": self.get_pending_invoices_count(),
            "expired_invoices_count": self.get_expired_invoices_count(),
            "paid_invoices_count": self.get_paid_invoices_count(),
            "unpaid_invoices_count": self.get_unpaid_invoices_count(),
            "cancelled_invoices_count": self.get_cancelled_invoices_count(),
            
            # Invoice revenue metrics
            "total_invoice_revenue": round(total_invoice_revenue, 2),
            "pending_invoice_revenue": round(pending_invoice_revenue, 2),
            
            # Invoice confirmation tracking
            "confirmed_invoices_count": confirmed_invoices,
            "unconfirmed_invoices_count": unconfirmed_invoices,
            
            # Invoice pickup tracking
            "picked_up_invoices_count": picked_up_invoices,
            "not_picked_up_invoices_count": not_picked_up_invoices,
        }
