from datetime import date, timedelta
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

        return {
            "stats": {
                "revenue_today": round(revenue_today, 2),
                "sales_count_today": sales_count_today,
                "trips_booked_today": trips_today,
                "courses_booked_today": courses_today,
                "pending_invoices_today": pending_today
            },
            "charts": {
                "sales_over_time": sales_chart_data,
                "activity_distribution": activity_distribution
            },
            "recent_transactions": recent_transactions
        }
        
    def get_dashboard_summary(self):
        """
        Aggregates all analytics for the main dashboard.
        """
        today = date.today()
        
        # --- 1. Today's Stats ---
        revenue_today = (
            self.db.query(func.sum(Invoice.amount))
            .filter(
                Invoice.status == "PAID",
                func.date(Invoice.updated_at) == today
            )
            .scalar() or 0.0
        )
        
        sales_count_today = (
            self.db.query(Invoice)
            .filter(
                Invoice.status == "PAID",
                func.date(Invoice.updated_at) == today
            )
            .count()
        )
        
        trips_today = (
            self.db.query(Invoice)
            .filter(
                Invoice.activity == "trip",
                func.date(Invoice.created_at) == today
            )
            .count()
        )
        
        courses_today = (
            self.db.query(Invoice)
            .filter(
                Invoice.activity == "course",
                func.date(Invoice.created_at) == today
            )
            .count()
        )

        pending_today = (
            self.db.query(Invoice)
            .filter(
                Invoice.status == "PENDING",
                func.date(Invoice.created_at) == today
            )
            .count()
        )

        # --- 2. Financial Health (New) ---
        # Total Revenue (All time PAID)
        total_paid_query = (
            self.db.query(func.sum(Invoice.amount), func.count(Invoice.id))
            .filter(Invoice.status == "PAID")
            .first()
        )
        total_revenue = total_paid_query[0] or 0.0
        total_paid_count = total_paid_query[1] or 0
        
        average_order_value = (total_revenue / total_paid_count) if total_paid_count > 0 else 0.0
        
        total_discount_given = (
            self.db.query(func.sum(Invoice.discount_amount))
            .filter(Invoice.status == "PAID")
            .scalar() or 0.0
        )
        
        potential_revenue = (
            self.db.query(func.sum(Invoice.amount))
            .filter(Invoice.status == "PENDING")
            .scalar() or 0.0
        )
        
        # --- 3. Chart Data (Last 30 Days) ---
        thirty_days_ago = today - timedelta(days=30)
        
        sales_data_query = (
            self.db.query(
                func.date(Invoice.updated_at).label("date"),
                func.sum(Invoice.amount).label("revenue"),
                func.count(Invoice.id).label("count")
            )
            .filter(
                Invoice.status == "PAID",
                Invoice.updated_at >= thirty_days_ago
            )
            .group_by(func.date(Invoice.updated_at))
            .order_by(func.date(Invoice.updated_at))
            .all()
        )
        
        sales_chart_data = [
            {
                "date": str(row.date),
                "revenue": round(row.revenue, 2),
                "count": row.count
            }
            for row in sales_data_query
        ]

        # --- 4. Distributions ---
        # Activity Distribution
        activity_dist_query = (
            self.db.query(
                Invoice.activity,
                func.count(Invoice.id)
            )
            .filter(Invoice.status == "PAID")
            .group_by(Invoice.activity)
            .all()
        )
        activity_distribution = [
            {"name": row[0].title(), "value": row[1]}
            for row in activity_dist_query
        ]
        
        # Payment Method Distribution (New)
        payment_method_query = (
            self.db.query(
                Invoice.payment_method,
                func.count(Invoice.id)
            )
            .filter(Invoice.status == "PAID")
            .group_by(Invoice.payment_method)
            .all()
        )
        # Handle cases where payment_method might be null (default to Online/EasyKash if not online/cash explicitly)
        payment_method_distribution = []
        for row in payment_method_query:
            pm_name = row[0] if row[0] else "Unknown"
            # Normalize names
            if pm_name == "easykash": pm_name = "Online (EasyKash)"
            elif pm_name == "cash": pm_name = "Cash"
            payment_method_distribution.append({"name": pm_name, "value": row[1]})

        # --- 5. Customer Insights (New) ---
        # Top 5 Customers by Spend

        # Wait, grouping by buyer_name might be unreliable if names are not unique. 
        # Better to group by user_id then join User? 
        # Let's group by User ID for accuracy, then fetch name.
        top_users_query = (
            self.db.query(
                User.first_name,
                User.last_name,
                User.email,
                func.sum(Invoice.amount).label("total_spent"),
                func.count(Invoice.id).label("invoice_count")
            )
            .join(Invoice, User.id == Invoice.user_id)
            .filter(Invoice.status == "PAID")
            .group_by(User.id)
            .order_by(func.sum(Invoice.amount).desc())
            .limit(5)
            .all()
        )
        
        top_customers = [
            {
                "name": f"{row.first_name} {row.last_name}",
                "email": row.email,
                "total_spent": round(row.total_spent, 2),
                "order_count": row.invoice_count
            }
            for row in top_users_query
        ]

        # --- 6. Operational Rate (New) ---
        # Confirmation status
        total_inv_count = self.db.query(Invoice).count() # Total created
        confirmed_count = self.db.query(Invoice).filter(Invoice.is_confirmed == True).count()
        confirmation_rate = (confirmed_count / total_inv_count * 100) if total_inv_count > 0 else 0.0

        # --- 7. Recent Transactions ---
        recent_transactions_query = (
            self.db.query(Invoice)
            .order_by(Invoice.created_at.desc())
            .limit(5)
            .all()
        )
        
        recent_transactions = [
            {
                "id": inv.id,
                "buyer": inv.buyer_name,
                "amount": inv.amount,
                "status": inv.status,
                "date": inv.created_at
            }
            for inv in recent_transactions_query
        ]

        return {
            "stats": {
                "revenue_today": round(revenue_today, 2),
                "sales_count_today": sales_count_today,
                "trips_booked_today": trips_today,
                "courses_booked_today": courses_today,
                "pending_invoices_today": pending_today,
                # New financial stats
                "average_order_value": round(average_order_value, 2),
                "total_discount_given": round(total_discount_given, 2),
                "potential_revenue": round(potential_revenue, 2),
                "confirmation_rate": round(confirmation_rate, 1)
            },
            "charts": {
                "sales_over_time": sales_chart_data,
                "activity_distribution": activity_distribution,
                "payment_method_distribution": payment_method_distribution
            },
            "top_customers": top_customers,
            "recent_transactions": recent_transactions
        }
