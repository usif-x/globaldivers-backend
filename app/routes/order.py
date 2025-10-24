from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_super_admin
from app.schemas.order import FilteredOrdersResponse, OrderFilter
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/filter", response_model=FilteredOrdersResponse)
def get_filtered_orders(
    filters: OrderFilter,
    db: Session = Depends(get_db),
):
    """
    Retrieves and filters invoices based on date range, activity, and status.
    - **start_date**: The start date for the filter range (YYYY-MM-DD).
    - **end_date**: The end date for the filter range (YYYY-MM-DD).
    - **activity**: The name of the activity to filter by (e.g., 'trip', 'course').
    - **status**: The status of the invoice to filter by (e.g., 'PAID', 'PENDING').
    - **picked_up**: Filter by whether the order has been picked up (true/false).
    - **user_id**: Filter by the ID of the user who created the invoice.
    - **buyer_email**: Filter by the email of the buyer.
    - **invoice_type**: Filter by the type of invoice ('online' or 'cash').
    """
    return OrderService.filter_invoices(db=db, filters=filters)
