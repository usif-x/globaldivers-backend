from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.invoice import InvoiceResponse


class OrderFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    activity: Optional[str] = None
    status: Optional[str] = None
    picked_up: Optional[bool] = None
    user_id: Optional[int] = None
    buyer_email: Optional[str] = None
    invoice_type: Optional[str] = None


class FilteredOrdersResponse(BaseModel):
    count: int
    total_amount: float
    invoices: List[InvoiceResponse]
