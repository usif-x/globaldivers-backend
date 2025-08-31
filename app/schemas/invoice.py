# app/schemas/invoice.py

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


# --- Existing schemas ---
class InvoiceBase(BaseModel):
    buyer_name: str
    buyer_email: str
    buyer_phone: str
    invoice_description: str
    activity: str
    picked_up: Optional[bool] = False
    amount: float
    currency: str


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceCreateResponse(BaseModel):
    id: int
    user_id: int
    status: str
    customer_reference: str
    pay_url: str
    created_at: datetime


class InvoiceResponse(InvoiceBase):
    id: int
    user_id: int
    status: str
    pay_url: Optional[str] = None
    activity: str
    picked_up: bool
    customer_reference: Optional[str] = None
    easykash_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Enhanced Admin Summary Schema ---
class InvoiceSummaryResponse(BaseModel):
    total_invoices: int
    total_revenue: float  # (Paid Amount)
    pending_count: int
    pending_amount_total: float  # <-- NEW
    paid_count: int
    failed_count: int
    failed_amount_total: float  # <-- NEW


# --- NEW User-Specific Summary Schema ---
class UserInvoiceSummaryResponse(BaseModel):
    total_invoices: int
    paid_invoices_count: int
    paid_amount_total: float
    pending_invoices_count: int
    pending_amount_total: float
    failed_invoices_count: int
    failed_amount_total: float


class InvoiceUpdate(BaseModel):
    buyer_name: Optional[str] = None
    buyer_email: Optional[EmailStr] = None
    buyer_phone: Optional[str] = None
    invoice_description: Optional[str] = None
    activity: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    picked_up: Optional[bool] = None
    status: Optional[str] = None  # Allow admins to manually change the status


class EasyKashCallbackPayload(BaseModel):
    ProductCode: str
    Amount: str
    ProductType: str
    PaymentMethod: str
    status: str
    easykashRef: str
    customerReference: str
    signatureHash: str

    # Make these optional since they might not always be sent
    BuyerName: Optional[str] = None
    BuyerEmail: Optional[str] = None
    BuyerMobile: Optional[str] = None
    Timestamp: Optional[str] = None
    voucher: Optional[str] = None
    VoucherData: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields
