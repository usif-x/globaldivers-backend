# app/schemas/invoice.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# Schema for data required to create an invoice
class InvoiceCreate(BaseModel):
    buyer_name: str
    buyer_email: EmailStr
    buyer_phone: str
    invoice_description: str
    activity: str
    amount: float
    currency: str


# Schema for the response after creating an invoice
class InvoiceCreateResponse(BaseModel):
    id: int
    user_id: int
    status: str
    customer_reference: str
    pay_url: str
    created_at: datetime

    class Config:
        orm_mode = True


# Schema for a full invoice response (e.g., for get_invoice)
class InvoiceResponse(BaseModel):
    id: int
    user_id: int
    buyer_name: str
    buyer_email: str
    buyer_phone: str
    invoice_description: str
    activity: str
    amount: float
    currency: str
    status: str
    customer_reference: Optional[str]
    easykash_reference: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class InvoiceSummaryResponse(BaseModel):
    total_invoices: int
    total_revenue: float
    pending_count: int
    paid_count: int
    failed_count: int

    class Config:
        from_attributes = True
