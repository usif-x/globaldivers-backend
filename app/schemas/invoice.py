# app/schemas/invoice.py

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- NEW Activity Detail Schema ---
class ActivityDetail(BaseModel):
    name: str = Field(
        ..., description="Name of the activity, e.g., 'Trip Booking: test'"
    )
    activity_date: date = Field(..., description="Date of the trip or activity")
    adults: int = Field(..., gt=0, description="Number of adults")
    children: int = Field(default=0, ge=0, description="Number of children")
    hotel_name: Optional[str] = Field(None, description="Name of the hotel for pickup")
    room_number: Optional[str] = Field(None, description="Room number for pickup")
    special_requests: Optional[str] = Field(
        None, description="Any special requests from the customer"
    )


# --- Existing schemas ---
class InvoiceBase(BaseModel):
    buyer_name: str
    buyer_email: str
    buyer_phone: str
    invoice_description: str
    activity: str
    activity_details: Optional[List[ActivityDetail]] = None
    picked_up: Optional[bool] = False
    amount: float
    currency: str
    invoice_type: str = Field(
        default="online", description="Type of invoice: 'online' or 'cash'"
    )


class InvoiceCreate(InvoiceBase):
    coupon_code: Optional[str] = None
    # --- NEW FIELDS FOR BACKEND VALIDATION ---
    trip_id: Optional[int] = Field(
        None,
        description="REQUIRED if activity='trip': The ID of the trip being booked",
    )
    course_id: Optional[int] = Field(
        None,
        description="REQUIRED if activity='course': The ID of the course being booked",
    )
    # For trips: number of adults and children
    adults: Optional[int] = Field(
        None,
        ge=0,
        description="REQUIRED if activity='trip': Number of adults (minimum 1)",
    )
    children: Optional[int] = Field(
        None,
        ge=0,
        description="Number of children (optional, must be 0 if trip doesn't allow children)",
    )


class InvoiceCreateResponse(BaseModel):
    id: int
    user_id: int
    status: str
    customer_reference: Optional[str] = None
    pay_url: Optional[str] = None
    invoice_type: str
    payment_method: Optional[str] = None
    created_at: datetime
    # --- NEW: Include discount and pricing details in response ---
    discount_breakdown: Optional[dict] = Field(
        None,
        description="Breakdown of all discounts applied (group discount, promo code, etc.)",
    )


class InvoiceResponse(InvoiceBase):
    id: int
    user_id: int
    status: str
    pay_url: Optional[str] = None
    activity: str
    activity_details: Optional[List[Any]] = None
    picked_up: bool
    customer_reference: Optional[str] = None
    easykash_reference: Optional[str] = None
    invoice_type: str
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # --- NEW: Include discount breakdown ---
    discount_breakdown: Optional[dict] = Field(
        None,
        description="Breakdown of all discounts applied",
    )
    # Admin fields
    is_confirmed: bool = Field(default=False, description="Admin confirmation status")
    notes: Optional[str] = Field(None, description="Admin-only notes for this customer")

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
    activity_details: Optional[List[ActivityDetail]] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    picked_up: Optional[bool] = None
    status: Optional[str] = None  # Allow admins to manually change the status
    invoice_type: Optional[str] = None
    is_confirmed: Optional[bool] = None  # Admin confirmation status
    notes: Optional[str] = None  # Admin-only notes


class EasyKashCallbackPayload(BaseModel):
    ProductCode: str
    Amount: str
    ProductType: str
    PaymentMethod: str
    status: str
    easykashRef: str
    customerReference: str
    signatureHash: str

    # Optional fields that are not part of the signature calculation
    BuyerName: Optional[str] = None
    BuyerEmail: Optional[str] = None
    BuyerMobile: Optional[str] = None
    Timestamp: Optional[str] = None
    voucher: Optional[str] = None
    VoucherData: Optional[str] = None

    class Config:
        # Allows other fields from EasyKash to be present without causing a validation error
        extra = "allow"


# --- NEW: Enhanced Analytics Schemas ---


class InvoiceActivityBreakdown(BaseModel):
    """Breakdown of invoices by activity type"""

    activity: str
    count: int
    total_revenue: float
    average_amount: float
    paid_count: int
    pending_count: int
    failed_count: int


class InvoicePaymentMethodBreakdown(BaseModel):
    """Breakdown of invoices by payment method"""

    payment_method: str
    count: int
    total_revenue: float
    success_rate: float  # Percentage of paid invoices


class InvoiceTypeBreakdown(BaseModel):
    """Breakdown of invoices by type (online/cash)"""

    invoice_type: str
    count: int
    total_revenue: float
    paid_count: int
    pending_count: int


class TopCustomerResponse(BaseModel):
    """Top customer by spending"""

    user_id: int
    buyer_name: str
    buyer_email: str
    total_invoices: int
    total_spent: float
    paid_invoices: int
    pending_invoices: int


class InvoiceDetailedSummaryResponse(BaseModel):
    """Comprehensive invoice analytics summary"""

    # Basic counts
    total_invoices: int
    confirmed_invoices: int
    unconfirmed_invoices: int

    # Status breakdown
    paid_count: int
    pending_count: int
    failed_count: int
    cancelled_count: int
    expired_count: int

    # Revenue metrics
    total_revenue: float  # Total paid amount
    pending_amount: float
    failed_amount: float
    average_invoice_amount: float

    # Conversion metrics
    conversion_rate: float  # Percentage of paid invoices
    payment_success_rate: float  # Paid / (Paid + Failed)

    # Breakdowns
    activity_breakdown: List[InvoiceActivityBreakdown]
    payment_method_breakdown: List[InvoicePaymentMethodBreakdown]
    invoice_type_breakdown: List[InvoiceTypeBreakdown]

    # Pickup tracking
    picked_up_count: int
    not_picked_up_count: int


class MonthlyInvoiceAnalytics(BaseModel):
    """Monthly invoice analytics with filtering"""

    month: str  # Format: "YYYY-MM"
    year: int
    month_number: int

    # Basic counts
    total_invoices: int
    confirmed_invoices: int
    unconfirmed_invoices: int

    # Status breakdown
    paid_count: int
    pending_count: int
    failed_count: int

    # Revenue
    total_revenue: float
    pending_amount: float
    average_invoice_amount: float

    # Conversion
    conversion_rate: float

    # Breakdowns
    activity_breakdown: List[InvoiceActivityBreakdown]
    payment_method_breakdown: List[InvoicePaymentMethodBreakdown]
    invoice_type_breakdown: List[InvoiceTypeBreakdown]

