from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.schemas.order import FilteredOrdersResponse, OrderFilter


class OrderService:
    @staticmethod
    def filter_invoices(db: Session, filters: OrderFilter) -> FilteredOrdersResponse:
        """
        Filters invoices based on the provided criteria.
        """
        query = db.query(Invoice)

        if filters.start_date:
            query = query.filter(Invoice.created_at >= filters.start_date)
        if filters.end_date:
            query = query.filter(Invoice.created_at <= filters.end_date)
        if filters.activity:
            query = query.filter(Invoice.activity.ilike(f"%{filters.activity}%"))
        if filters.status:
            query = query.filter(Invoice.status == filters.status)
        if filters.picked_up is not None:
            query = query.filter(Invoice.picked_up == filters.picked_up)
        if filters.user_id:
            query = query.filter(Invoice.user_id == filters.user_id)
        if filters.buyer_email:
            query = query.filter(Invoice.buyer_email.ilike(f"%{filters.buyer_email}%"))

        invoices = query.order_by(Invoice.created_at.desc()).all()

        total_amount = query.with_entities(func.sum(Invoice.amount)).scalar()

        return FilteredOrdersResponse(
            count=len(invoices),
            total_amount=round(total_amount or 0.0, 2),
            invoices=invoices,
        )
