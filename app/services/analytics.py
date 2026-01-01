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
            .scalar()
            or 0.0
        )
        pending_invoice_revenue = (
            self.db.query(func.sum(Invoice.amount))
            .filter(Invoice.status == "PENDING")
            .scalar()
            or 0.0
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
                "pending_invoices_today": pending_today,
            },
            "charts": {
                "sales_over_time": sales_chart_data,
                "activity_distribution": activity_distribution,
            },
            "recent_transactions": recent_transactions,
        }

    def get_dashboard_summary(self, month: int = None, year: int = None):
        """
        Enhanced analytics for dashboard with monthly filter, correct sales, best sellers, top courses/activities, and charted data.
        Returns a dict with stats, charts, top lists, and best sellers.
        """
        today = date.today()
        is_filtered_view = month is not None and year is not None
        start_date = None
        end_date = None
        if is_filtered_view:
            try:
                start_date = date(year, month, 1)
                end_date = (
                    date(year + 1, 1, 1) - timedelta(days=1)
                    if month == 12
                    else date(year, month + 1, 1) - timedelta(days=1)
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid month or year")

        def apply_date_filter(query, column):
            if is_filtered_view:
                return query.filter(
                    func.date(column) >= start_date, func.date(column) <= end_date
                )
            else:
                return query.filter(func.date(column) == today)

        def apply_general_filter(query, column=Invoice.updated_at):
            if is_filtered_view:
                return query.filter(
                    func.date(column) >= start_date, func.date(column) <= end_date
                )
            else:
                return query

        # Revenue and sales
        revenue_val = (
            apply_date_filter(
                self.db.query(func.sum(Invoice.amount)).filter(
                    Invoice.status == "PAID"
                ),
                Invoice.updated_at,
            ).scalar()
            or 0.0
        )
        sales_count_val = apply_date_filter(
            self.db.query(Invoice).filter(Invoice.status == "PAID"), Invoice.updated_at
        ).count()
        trips_val = apply_date_filter(
            self.db.query(Invoice).filter(Invoice.activity == "trip"),
            Invoice.created_at,
        ).count()
        courses_val = apply_date_filter(
            self.db.query(Invoice).filter(Invoice.activity == "course"),
            Invoice.created_at,
        ).count()
        pending_val = apply_date_filter(
            self.db.query(Invoice).filter(Invoice.status == "PENDING"),
            Invoice.created_at,
        ).count()

        # Financials
        total_paid_query = self.db.query(
            func.sum(Invoice.amount), func.count(Invoice.id)
        ).filter(Invoice.status == "PAID")
        total_paid_query = apply_general_filter(total_paid_query)
        total_paid_res = total_paid_query.first()
        total_revenue_context = total_paid_res[0] or 0.0
        total_count_context = total_paid_res[1] or 0
        average_order_value = (
            (total_revenue_context / total_count_context)
            if total_count_context > 0
            else 0.0
        )
        total_discount_given = (
            apply_general_filter(
                self.db.query(func.sum(Invoice.discount_amount)).filter(
                    Invoice.status == "PAID"
                )
            ).scalar()
            or 0.0
        )
        potential_rev_query = self.db.query(func.sum(Invoice.amount)).filter(
            Invoice.status == "PENDING"
        )
        if is_filtered_view:
            potential_rev_query = potential_rev_query.filter(
                func.date(Invoice.created_at) >= start_date,
                func.date(Invoice.created_at) <= end_date,
            )
        potential_revenue = potential_rev_query.scalar() or 0.0

        # Chart data
        chart_start_date = (
            start_date if is_filtered_view else (today - timedelta(days=30))
        )
        chart_end_date = end_date if is_filtered_view else today
        sales_data_query = self.db.query(
            func.date(Invoice.updated_at).label("date"),
            func.sum(Invoice.amount).label("revenue"),
            func.count(Invoice.id).label("count"),
        ).filter(
            Invoice.status == "PAID", func.date(Invoice.updated_at) >= chart_start_date
        )
        if is_filtered_view or chart_end_date:
            sales_data_query = sales_data_query.filter(
                func.date(Invoice.updated_at) <= (chart_end_date or today)
            )
        sales_data_query = (
            sales_data_query.group_by(func.date(Invoice.updated_at))
            .order_by(func.date(Invoice.updated_at))
            .all()
        )
        sales_chart_data = [
            {
                "date": str(row.date),
                "revenue": round(row.revenue, 2),
                "count": row.count,
            }
            for row in sales_data_query
        ]

        # Activity distribution
        # First, get count per activity
        activity_counts = self.db.query(
            Invoice.activity,
            func.count(Invoice.id).label("count"),
        ).filter(Invoice.status == "PAID")
        activity_counts = apply_general_filter(activity_counts)
        activity_counts = activity_counts.group_by(Invoice.activity).all()

        activity_distribution = []
        for row in activity_counts:
            # Get one representative invoice for this activity to extract the name
            sample_invoice = (
                self.db.query(Invoice.activity_details)
                .filter(Invoice.status == "PAID", Invoice.activity == row.activity)
                .first()
            )
            details = (
                sample_invoice.activity_details[0]
                if sample_invoice
                and sample_invoice.activity_details
                and isinstance(sample_invoice.activity_details, list)
                and len(sample_invoice.activity_details) > 0
                else {}
            )
            activity_name = (
                details.get("name")
                or details.get("activity_name")
                or row.activity.title()
            )
            activity_distribution.append({"name": activity_name, "value": row.count})

        # Payment method distribution
        payment_method_query = self.db.query(
            Invoice.payment_method, func.count(Invoice.id)
        ).filter(Invoice.status == "PAID")
        payment_method_query = apply_general_filter(payment_method_query)
        payment_method_query = payment_method_query.group_by(
            Invoice.payment_method
        ).all()
        payment_method_distribution = []
        for row in payment_method_query:
            pm_name = row[0] if row[0] else "Unknown"
            if pm_name == "easykash":
                pm_name = "Online (EasyKash)"
            elif pm_name == "cash":
                pm_name = "Cash"
            payment_method_distribution.append({"name": pm_name, "value": row[1]})

        # Top customers
        top_users_query = (
            self.db.query(
                User.full_name,
                User.email,
                func.sum(Invoice.amount).label("total_spent"),
                func.count(Invoice.id).label("invoice_count"),
            )
            .join(Invoice, User.id == Invoice.user_id)
            .filter(Invoice.status == "PAID")
        )
        top_users_query = apply_general_filter(top_users_query)
        top_users_query = (
            top_users_query.group_by(User.id)
            .order_by(func.sum(Invoice.amount).desc())
            .limit(5)
            .all()
        )
        top_customers = [
            {
                "name": row.full_name,
                "email": row.email,
                "total_spent": round(row.total_spent, 2),
                "order_count": row.invoice_count,
            }
            for row in top_users_query
        ]

        # Top courses sold
        top_courses_query = self.db.query(
            Invoice.activity_details,
            func.sum(Invoice.amount).label("total_revenue"),
            func.count(Invoice.id).label("sales_count"),
        ).filter(Invoice.status == "PAID", Invoice.activity == "course")
        if is_filtered_view:
            top_courses_query = top_courses_query.filter(
                func.date(Invoice.updated_at) >= start_date,
                func.date(Invoice.updated_at) <= end_date,
            )
        top_courses_query = (
            top_courses_query.group_by(Invoice.activity_details)
            .order_by(func.sum(Invoice.amount).desc())
            .limit(5)
            .all()
        )
        top_courses = []
        for row in top_courses_query:
            # Try to extract course name from activity_details JSON
            details = (
                row.activity_details[0]
                if row.activity_details
                and isinstance(row.activity_details, list)
                and len(row.activity_details) > 0
                else {}
            )
            course_name = details.get("name") or details.get("course_name") or "Unknown"
            top_courses.append(
                {
                    "course_name": course_name,
                    "total_revenue": round(row.total_revenue, 2),
                    "sales_count": row.sales_count,
                }
            )

        # Top activities sold (by activity type)
        top_activities_query = self.db.query(
            Invoice.activity,
            func.sum(Invoice.amount).label("total_revenue"),
            func.count(Invoice.id).label("sales_count"),
        ).filter(Invoice.status == "PAID")
        if is_filtered_view:
            top_activities_query = top_activities_query.filter(
                func.date(Invoice.updated_at) >= start_date,
                func.date(Invoice.updated_at) <= end_date,
            )
        top_activities_query = (
            top_activities_query.group_by(Invoice.activity)
            .order_by(func.sum(Invoice.amount).desc())
            .limit(5)
            .all()
        )
        top_activities = []
        for row in top_activities_query:
            # Get one representative invoice for this activity to extract the name
            sample_invoice = (
                self.db.query(Invoice.activity_details)
                .filter(Invoice.status == "PAID", Invoice.activity == row.activity)
                .first()
            )
            details = (
                sample_invoice.activity_details[0]
                if sample_invoice
                and sample_invoice.activity_details
                and isinstance(sample_invoice.activity_details, list)
                and len(sample_invoice.activity_details) > 0
                else {}
            )
            activity_name = (
                details.get("name")
                or details.get("activity_name")
                or row.activity.title()
            )
            top_activities.append(
                {
                    "activity": activity_name,
                    "total_revenue": round(row.total_revenue, 2),
                    "sales_count": row.sales_count,
                }
            )

        # Best selling month (all time)
        best_month_query = self.db.query(
            func.extract("year", Invoice.updated_at).label("year"),
            func.extract("month", Invoice.updated_at).label("month"),
            func.sum(Invoice.amount).label("revenue"),
        ).filter(Invoice.status == "PAID")
        best_month_query = (
            best_month_query.group_by("year", "month")
            .order_by(func.sum(Invoice.amount).desc())
            .first()
        )
        best_month = None
        if best_month_query:
            best_month = {
                "year": int(best_month_query.year),
                "month": int(best_month_query.month),
                "revenue": round(best_month_query.revenue, 2),
            }

        # Confirmation rate
        total_inv_q = self.db.query(Invoice)
        confirmed_inv_q = self.db.query(Invoice).filter(Invoice.is_confirmed == True)
        total_inv_q = apply_general_filter(total_inv_q, Invoice.created_at)
        confirmed_inv_q = apply_general_filter(confirmed_inv_q, Invoice.created_at)
        total_inv_count = total_inv_q.count()
        confirmed_count = confirmed_inv_q.count()
        confirmation_rate = (
            (confirmed_count / total_inv_count * 100) if total_inv_count > 0 else 0.0
        )

        # Recent transactions
        recent_trans_query = self.db.query(Invoice)
        if is_filtered_view:
            recent_trans_query = recent_trans_query.filter(
                func.date(Invoice.created_at) >= start_date,
                func.date(Invoice.created_at) <= end_date,
            )
        recent_transactions_query = (
            recent_trans_query.order_by(Invoice.created_at.desc()).limit(5).all()
        )
        recent_transactions = [
            {
                "id": inv.id,
                "buyer": inv.buyer_name,
                "amount": inv.amount,
                "status": inv.status,
                "date": inv.created_at,
            }
            for inv in recent_transactions_query
        ]

        return {
            "stats": {
                "revenue": round(revenue_val, 2),
                "sales_count": sales_count_val,
                "trips_booked": trips_val,
                "courses_booked": courses_val,
                "pending_invoices": pending_val,
                "average_order_value": round(average_order_value, 2),
                "total_discount_given": round(total_discount_given, 2),
                "potential_revenue": round(potential_revenue, 2),
                "confirmation_rate": round(confirmation_rate, 1),
                "best_selling_month": best_month,
            },
            "charts": {
                "sales_over_time": sales_chart_data,
                "activity_distribution": activity_distribution,
                "payment_method_distribution": payment_method_distribution,
            },
            "top_customers": top_customers,
            "top_courses": top_courses,
            "top_activities": top_activities,
            "recent_transactions": recent_transactions,
            # --- More detailed analytics ---
            "users": {
                "total": self.get_users_count(),
                "active": self.get_active_users_count(),
                "inactive": self.get_inactive_users_count(),
                "blocked": self.get_blocked_users_count(),
                "unblocked": self.get_unblocked_users_count(),
            },
            "testimonials": {
                "total": self.get_testimonials_count(),
                "accepted": self.get_accepted_testimonials_count(),
                "unaccepted": self.get_unaccepted_testimonials_count(),
            },
            "content": {
                "trips": self.get_trips_count(),
                "packages": self.get_packages_count(),
                "courses": self.get_courses_count(),
            },
            "invoices": {
                "total": self.get_invoices_count(),
                "pending": self.get_pending_invoices_count(),
                "expired": self.get_expired_invoices_count(),
                "paid": self.get_paid_invoices_count(),
                "unpaid": self.get_unpaid_invoices_count(),
                "cancelled": self.get_cancelled_invoices_count(),
                "confirmed": self.db.query(Invoice)
                .filter(Invoice.is_confirmed == True)
                .count(),
                "unconfirmed": self.db.query(Invoice)
                .filter(Invoice.is_confirmed == False)
                .count(),
                "picked_up": self.db.query(Invoice)
                .filter(Invoice.picked_up == True)
                .count(),
                "not_picked_up": self.db.query(Invoice)
                .filter(Invoice.picked_up == False)
                .count(),
                "total_invoice_revenue": float(
                    self.db.query(func.sum(Invoice.amount))
                    .filter(Invoice.status == "PAID")
                    .scalar()
                    or 0.0
                ),
                "pending_invoice_revenue": float(
                    self.db.query(func.sum(Invoice.amount))
                    .filter(Invoice.status == "PENDING")
                    .scalar()
                    or 0.0
                ),
            },
        }
