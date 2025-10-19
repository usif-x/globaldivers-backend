from fastapi import HTTPException
from sqlalchemy import select
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
        return {
            "users_count": self.get_users_count(),
            "active_users_count": self.get_active_users_count(),
            "inactive_users_count": self.get_inactive_users_count(),
            "blocked_users_count": self.get_blocked_users_count(),
            "unblocked_users_count": self.get_unblocked_users_count(),
            "trips_count": self.get_trips_count(),
            "packages_count": self.get_packages_count(),
            "testimonials_count": self.get_testimonials_count(),
            "accepted_testimonials_count": self.get_accepted_testimonials_count(),
            "unaccepted_testimonials_count": self.get_unaccepted_testimonials_count(),
            "courses_count": self.get_courses_count(),
            "invoices_count": self.get_invoices_count(),
            "pending_invoices_count": self.get_pending_invoices_count(),
            "expired_invoices_count": self.get_expired_invoices_count(),
            "paid_invoices_count": self.get_paid_invoices_count(),
            "unpaid_invoices_count": self.get_unpaid_invoices_count(),
            "cancelled_invoices_count": self.get_cancelled_invoices_count(),
        }
