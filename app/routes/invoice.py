# app/routers/invoice.py

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_super_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User
from app.schemas.invoice import InvoiceSummaryResponse  # <-- Make sure this is imported
from app.schemas.invoice import InvoiceCreate, InvoiceCreateResponse, InvoiceResponse
from app.services.invoice import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


# --- User-Facing Routes ---


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=InvoiceCreateResponse,
    summary="Create a new invoice and payment link",
)
def create_new_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new invoice associated with the currently logged-in user.
    """
    invoice = InvoiceService.create_invoice(db, invoice_data, current_user.id)
    return invoice


@router.get(
    "/me",
    response_model=List[InvoiceResponse],
    summary="Get all invoices for the current user",
)
def get_my_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a list of all invoices belonging to the currently authenticated user.
    """
    return InvoiceService.get_my_invoices_for_user(db=db, user_id=current_user.id)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get a specific invoice by ID",
)
def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details for a specific invoice.

    **Security**: This endpoint ensures that users can only access their own invoices.
    """
    # [SECURITY FIX] Pass the current_user.id to the service layer for validation.
    invoice = InvoiceService.get_invoice(db, invoice_id, current_user.id)
    return invoice


# --- Admin-Only Routes ---


@router.get(
    "/admin/summary",
    response_model=InvoiceSummaryResponse,
    summary="Get an analytics summary of all invoices (Admin Only)",
    dependencies=[Depends(get_current_super_admin)],
)
def get_invoices_summary_for_admin(db: Session = Depends(get_db)):
    """
    Provides a summary of all invoices in the system, including total revenue
    and counts by status. Requires super admin privileges.
    """
    return InvoiceService.get_invoices_summary_for_admin(db=db)


@router.get(
    "/{invoice_id}/admin",
    response_model=InvoiceResponse,
    summary="Get a specific invoice by ID",
    dependencies=[Depends(get_current_super_admin)],
)
def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve details for a specific invoice.

    **Security**: This endpoint ensures that users can only access their own invoices.
    """
    # [SECURITY FIX] Pass the current_user.id to the service layer for validation.
    invoice = InvoiceService.get_invoice_admin(db, invoice_id)
    return invoice


@router.get(
    "/admin/all",
    response_model=List[InvoiceResponse],
    summary="Get all invoices in the system (Admin Only)",
    dependencies=[Depends(get_current_super_admin)],
)
def get_all_invoices_for_admin(
    skip: int = 0,
    limit: int = 100,
    search: str = None,  # <-- [NEW] Add optional search query parameter
    db: Session = Depends(get_db),
):
    """
    Retrieves a paginated list of all invoices. Requires super admin privileges.
    Can be filtered by `search` on the customer reference.
    """
    return InvoiceService.get_all_invoices_for_admin(
        db=db, skip=skip, limit=limit, search=search  # <-- [NEW] Pass search to service
    )
