from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceList,
    InvoiceResponse,
    InvoiceStatus,
    InvoiceStatusUpdate,
    InvoiceSummary,
    InvoiceUpdate,
    UserResponse,
)
from app.services.invoice import InvoiceService

invoice_routes = APIRouter(prefix="/invoices", tags=["invoices Endpoints"])


# USER ROUTES - Require user authentication
@invoice_routes.post("/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new invoice for the current user"""
    # Ensure user can only create invoices for themselves (unless admin)
    if invoice_data.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="You can only create invoices for yourself"
        )

    invoice_service = InvoiceService(db)
    return await invoice_service.create_invoice(invoice_data)


@invoice_routes.get("/", response_model=InvoiceList)
async def get_all_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """Get all invoices with pagination (admin function)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_all_invoices(
        page=page, per_page=per_page, status=status
    )


@invoice_routes.get("/my", response_model=InvoiceList)
async def get_my_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's invoices with pagination"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_invoices_by_user(
        user_id=current_user.id, page=page, per_page=per_page, status=status
    )


@invoice_routes.get("/my/summary", response_model=InvoiceSummary)
async def get_my_invoice_summary(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get current user's invoice summary/analytics"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_invoice_summary(user_id=current_user.id)


@invoice_routes.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific invoice (users can only access their own invoices)"""
    invoice_service = InvoiceService(db)
    invoice = await invoice_service.get_invoice_by_id(invoice_id)

    # Check if user owns this invoice (unless admin)
    if invoice.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="You can only access your own invoices"
        )

    return invoice


@invoice_routes.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_data: InvoiceUpdate,
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an invoice (users can only update their own invoices)"""
    invoice_service = InvoiceService(db)

    # First check if invoice exists and user owns it
    existing_invoice = await invoice_service.get_invoice_by_id(invoice_id)
    if existing_invoice.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="You can only update your own invoices"
        )

    # Users cannot update paid invoices
    if (
        existing_invoice.status == InvoiceStatus.PAID.value
        and not current_user.is_admin
    ):
        raise HTTPException(status_code=400, detail="Cannot update a paid invoice")

    return await invoice_service.update_invoice(invoice_id, invoice_data)


@invoice_routes.patch("/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    status_data: InvoiceStatusUpdate,
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update invoice status (limited user access)"""
    invoice_service = InvoiceService(db)

    # Check if user owns this invoice
    existing_invoice = await invoice_service.get_invoice_by_id(invoice_id)
    if existing_invoice.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="You can only update your own invoices"
        )

    # Users can only cancel their own pending invoices, admins can do more
    if not current_user.is_admin:
        if status_data.status != InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=403, detail="Users can only cancel their invoices"
            )
        if existing_invoice.status != InvoiceStatus.PENDING.value:
            raise HTTPException(
                status_code=400, detail="You can only cancel pending invoices"
            )

    return await invoice_service.update_invoice_status(invoice_id, status_data)


# ADMIN ROUTES - Require admin authentication
@invoice_routes.get("/admin/all", response_model=InvoiceList)
async def get_all_invoices_admin(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get all invoices with pagination (Admin only)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_all_invoices(
        page=page, per_page=per_page, status=status
    )


@invoice_routes.get("/admin/user/{user_id}", response_model=InvoiceList)
async def get_user_invoices_admin(
    user_id: int = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get invoices for a specific user (Admin only)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_invoices_by_user(
        user_id=user_id, page=page, per_page=per_page, status=status
    )


@invoice_routes.get("/admin/summary", response_model=InvoiceSummary)
async def get_invoice_summary_admin(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get invoice summary/analytics for all users or specific user (Admin only)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_invoice_summary(user_id=user_id)


@invoice_routes.get("/admin/status/{status}", response_model=list[InvoiceResponse])
async def get_invoices_by_status_admin(
    status: InvoiceStatus = Path(..., description="Invoice status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get all invoices with specific status (Admin only)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.get_invoices_by_status(status)


@invoice_routes.patch("/admin/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status_admin(
    status_data: InvoiceStatusUpdate,
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update invoice status (Admin only - full access)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.update_invoice_status(invoice_id, status_data)


@invoice_routes.patch("/admin/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice_admin(
    invoice_data: InvoiceUpdate,
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update any invoice (Admin only)"""
    invoice_service = InvoiceService(db)
    return await invoice_service.update_invoice(invoice_id, invoice_data)


@invoice_routes.delete("/admin/{invoice_id}")
async def delete_invoice_admin(
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete/Cancel an invoice (Admin only)"""
    invoice_service = InvoiceService(db)
    success = await invoice_service.delete_invoice(invoice_id)

    if success:
        return {"message": "Invoice cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to cancel invoice")


@invoice_routes.post("/admin/expire-pending")
async def expire_pending_invoices_admin(
    days_old: int = Query(
        7, ge=1, description="Number of days old to consider for expiration"
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Expire old pending invoices (Admin only)"""
    invoice_service = InvoiceService(db)
    expired_count = await invoice_service.expire_pending_invoices(days_old)

    return {"message": f"Expired {expired_count} pending invoices"}


# PAYMENT WEBHOOK ROUTES - These might need special authentication or API keys
@invoice_routes.post("/webhook/payment-success/{invoice_id}")
async def payment_success_webhook(
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    # Note: Add proper webhook authentication here
):
    """Handle payment success webhook"""
    invoice_service = InvoiceService(db)
    return await invoice_service.mark_invoice_as_paid(invoice_id)


@invoice_routes.post("/webhook/payment-failed/{invoice_id}")
async def payment_failed_webhook(
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    # Note: Add proper webhook authentication here
):
    """Handle payment failure webhook"""
    invoice_service = InvoiceService(db)
    return await invoice_service.mark_invoice_as_failed(invoice_id)
