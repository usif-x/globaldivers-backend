from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    FAWRY = "fawry"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"


class InvoiceFor(str, Enum):
    COURSE = "course"
    TRIP = "trip"
    SERVICE = "service"
    OTHER = "other"


# Simple User schema for invoice response
class UserResponse(BaseModel):
    """Simple user schema for invoice responses"""

    id: int
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Schema for creating a new invoice"""

    user_id: int = Field(
        ..., description="ID of the user for whom the invoice is created"
    )
    amount: float = Field(..., ge=0.01, description="Total amount of the invoice")
    status: InvoiceStatus = Field(
        default=InvoiceStatus.PENDING, description="Status of the invoice"
    )
    pay_method: PaymentMethod = Field(..., description="Payment method for the invoice")
    invoice_for: InvoiceFor = Field(..., description="What the invoice is for")
    items: List[dict] = Field(
        ..., min_items=1, description="List of items in the invoice"
    )
    pay_url: Optional[str] = Field(
        None, description="Payment URL (will be generated if not provided)"
    )

    @validator("amount")
    def validate_amount_matches_items(cls, v, values):
        if "items" in values:
            # Handle case where items might have different structures
            total_from_items = 0
            for item in values["items"]:
                if isinstance(item, dict):
                    # Try different possible field names for price
                    price = (
                        item.get("total_price")
                        or item.get("price")
                        or item.get("amount", 0)
                    )
                    total_from_items += float(price)
                else:
                    # If items have total_price attribute
                    total_from_items += getattr(item, "total_price", 0)

            if (
                abs(v - total_from_items) > 0.01
            ):  # Allow for small floating point differences
                raise ValueError("amount must equal the sum of all item prices")
        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating an existing invoice"""

    status: Optional[InvoiceStatus] = Field(
        None, description="Updated status of the invoice"
    )
    pay_url: Optional[str] = Field(None, description="Updated payment URL")
    pay_method: Optional[PaymentMethod] = Field(
        None, description="Updated payment method"
    )
    amount: Optional[float] = Field(None, ge=0.01, description="Updated total amount")
    items: Optional[List[dict]] = Field(
        None, min_items=1, description="Updated list of items"
    )

    @validator("amount")
    def validate_amount_matches_items(cls, v, values):
        if v is not None and "items" in values and values["items"] is not None:
            total_from_items = 0
            for item in values["items"]:
                if isinstance(item, dict):
                    price = (
                        item.get("total_price")
                        or item.get("price")
                        or item.get("amount", 0)
                    )
                    total_from_items += float(price)
                else:
                    total_from_items += getattr(item, "total_price", 0)

            if abs(v - total_from_items) > 0.01:
                raise ValueError("amount must equal the sum of all item prices")
        return v


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""

    id: int
    user_id: int
    amount: float
    status: str
    pay_url: str
    pay_method: str
    invoice_for: str
    items: List[dict]  # Using dict for flexibility with existing data
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None  # Use UserResponse instead of User model

    class Config:
        from_attributes = True


class InvoiceList(BaseModel):
    """Schema for paginated invoice list response"""

    invoices: List[InvoiceResponse]
    total: int
    page: int
    per_page: int
    pages: int


class InvoiceStatusUpdate(BaseModel):
    """Schema specifically for updating invoice status"""

    status: InvoiceStatus = Field(..., description="New status for the invoice")
    pay_url: Optional[str] = Field(
        None, description="Payment URL if status is being updated due to payment"
    )


class InvoiceSummary(BaseModel):
    """Schema for invoice summary/analytics"""

    total_invoices: int
    total_amount: float
    pending_invoices: int
    pending_amount: float
    paid_invoices: int
    paid_amount: float
    failed_invoices: int
    failed_amount: float
