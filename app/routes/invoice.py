# app/routers/invoice.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_super_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User

# --- IMPORT NEW AND UPDATED SCHEMAS ---
from app.schemas.invoice import UserInvoiceSummaryResponse  # <-- NEW
from app.schemas.invoice import (
    EasyKashCallbackPayload,
    InvoiceCreate,
    InvoiceCreateResponse,
    InvoiceResponse,
    InvoiceSummaryResponse,
    InvoiceUpdate,
)
from app.services.invoice import InvoiceService
from app.utils.easykash import easykash_client

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
    return InvoiceService.get_my_invoices_for_user(db=db, user_id=current_user.id)


# --- NEW User Summary Route ---
@router.get(
    "/me/summary",
    response_model=UserInvoiceSummaryResponse,
    summary="Get an analytics summary of the current user's invoices",
)
def get_my_invoices_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Provides a detailed summary of the current user's invoices, including
    counts and total amounts for paid, pending, and failed statuses.
    """
    return InvoiceService.get_summary_for_user(db=db, user_id=current_user.id)


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
    invoice = InvoiceService.get_invoice(db, invoice_id, current_user.id)
    return invoice


@router.get(
    "/me/last",
    response_model=InvoiceResponse,
    summary="Get the last created invoice for the current user",
)
def get_last_invoice_for_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the most recently created invoice for the currently authenticated user.
    Ideal for redirecting a user to check the status immediately after a booking.
    """
    return InvoiceService.get_last_invoice_for_user(db=db, user_id=current_user.id)


@router.get(
    "/by-reference/{customer_reference}",
    response_model=InvoiceResponse,
    summary="Get a specific invoice by its customer reference",
)
def get_invoice_by_reference(
    customer_reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves details for a specific invoice using its `customerReference`.
    **Security**: This endpoint ensures that a user can only access their own invoice.
    """
    return InvoiceService.get_invoice_by_reference_for_user(
        db=db, customer_reference=customer_reference, user_id=current_user.id
    )


# --- Admin-Only Routes ---

# ... other admin routes are unchanged ...


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
def get_invoice_details_for_admin(  # Renamed function to avoid conflict
    invoice_id: int,
    db: Session = Depends(get_db),
):
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
    search: str = None,
    db: Session = Depends(get_db),
):
    return InvoiceService.get_all_invoices_for_admin(
        db=db, skip=skip, limit=limit, search=search
    )


@router.put(
    "/admin/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update an invoice (Admin Only)",
    dependencies=[Depends(get_current_super_admin)],
)
def update_invoice_for_admin(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
):
    """
    Allows a super admin to update any field of an existing invoice.
    """
    return InvoiceService.update_invoice_admin(
        db=db, invoice_id=invoice_id, invoice_data=invoice_data
    )


# --- NEW Admin Delete Route ---
@router.delete(
    "/admin/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an invoice (Admin Only)",
    dependencies=[Depends(get_current_super_admin)],
)
def delete_invoice_for_admin(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """
    Allows a super admin to permanently delete an invoice. Use with caution.
    """
    InvoiceService.delete_invoice_admin(db=db, invoice_id=invoice_id)
    return  # Returns 204 No Content on success


@router.get(
    "/invoice/picked-up",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_super_admin)],
)
def update_invoice_picked_up_status(
    invoice_id: int,
    picked_up: bool,
    db: Session = Depends(get_db),
):
    return InvoiceService.update_invoice_picked_up_status(
        db=db, invoice_id=invoice_id, picked_up=picked_up
    )


@router.post(
    "/webhook/create-easykash-callback",
    summary="Handle payment callbacks from EasyKash",
    status_code=status.HTTP_200_OK,
)
def handle_easykash_webhook():
    return InvoiceService.create_callback_data()


@router.post(
    "/webhook/easykash-callback",
    summary="Handle payment callbacks from EasyKash",
    status_code=status.HTTP_200_OK,
)
def handle_easykash_webhook(
    payload: EasyKashCallbackPayload,
    db: Session = Depends(get_db),
):
    """
    This public endpoint receives notifications from EasyKash.
    It verifies the signature and updates the invoice status accordingly.
    """
    # 1. Verify the signature first. This is the security gate.
    is_valid = easykash_client.verify_callback(payload.model_dump())

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature. Callback rejected.",
        )

    # 2. If the signature is valid, process the payment.
    return InvoiceService.process_payment_callback(db=db, payload=payload)
