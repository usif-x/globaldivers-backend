# app/routers/invoice.py

import json
import os
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, status
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

load_dotenv

EASYKASH_SECRET_KEY = os.environ.get("EASYKASH_SECRET_KEY")

router = APIRouter(prefix="/invoices", tags=["Invoices"])


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
    "/webhook/test-easykash-callback",
    summary="Handle payment callbacks from EasyKash",
    status_code=status.HTTP_200_OK,
)
def handle_easykash_webhook():
    if easykash_client.verify_example_callback():
        return {"message": "Example callback processed successfully"}
    else:
        return {"message": "Example callback verification failed"}


@router.post("/webhook/easykash-callback", status_code=status.HTTP_200_OK)
async def easykash_callback_handler(
    payload: EasyKashCallbackPayload, db: Session = Depends(get_db)
):
    """
    Receives, verifies, and processes payment callbacks from EasyKash.

    Workflow:
    1.  Validates the HMAC signature to ensure the request is authentic.
    2.  If the signature is valid, it calls the Invoice processing logic.
    3.  Handles errors gracefully and returns appropriate HTTP status codes.
    """
    # --- Step 0: Pre-flight Check ---
    # Ensure the server is configured with the secret key.
    if not EASYKASH_SECRET_KEY:
        print(
            "FATAL SERVER ERROR: EASYKASH_SECRET_KEY is not set in environment variables."
        )
        # Do not expose details to the client. This is a server configuration issue.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is not configured to handle callbacks.",
        )

    # --- Step 1: Security - Verify the Signature (The Gatekeeper) ---
    is_signature_valid = easykash_client.verify_official_callback(
        payload, EASYKASH_SECRET_KEY
    )

    if not is_signature_valid:
        # If the signature doesn't match, reject the request immediately.
        # This prevents any processing of tampered or unauthorized data.
        print(
            f"WARNING: Invalid signature received for customer reference '{payload.customerReference}'."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature hash. Request rejected.",
        )

    print(
        f"Signature verified successfully for customer reference: {payload.customerReference}"
    )

    # --- Step 2: Business Logic - Process the Payment (The Worker) ---
    # The payload is now trusted. We can safely pass it to your function.
    # Your `process_payment_callback` function handles its own exceptions (like 404),
    # so we can let them bubble up. We add a generic catch for unexpected errors.
    try:
        result = InvoiceService.process_payment_callback(db=db, payload=payload)
        return result
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions raised from your processing function (e.g., the 404)
        raise http_exc
    except Exception as e:
        # Catch any other unexpected database or application errors.
        print(
            f"ERROR: An unexpected error occurred while processing payment for ref '{payload.customerReference}': {e}"
        )
        db.rollback()  # Rollback transaction on unexpected failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while updating the invoice.",
        )
