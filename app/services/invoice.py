# app/services/invoice_service.py

from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.schemas.invoice import (
    InvoiceSummaryResponse,  # <-- You will need to create this schema
)
from app.schemas.invoice import InvoiceCreate, InvoiceCreateResponse, InvoiceResponse
from app.utils.easykash import easykash_client


class InvoiceService:
    @staticmethod
    def create_invoice(
        db: Session, invoice_data: InvoiceCreate, user_id: int
    ) -> InvoiceCreateResponse:
        """
        1. Creates a payment link with EasyKash.
        2. If successful, saves an invoice record to the database.
        3. Returns the new invoice details including the payment URL.
        """
        payment_payload = invoice_data.model_dump()
        easykash_response = easykash_client.create_payment(
            payment_data=payment_payload, user_id=user_id
        )

        if not easykash_response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create payment link: {easykash_response.get('details')}",
            )

        new_invoice = Invoice(
            user_id=user_id,
            buyer_name=invoice_data.buyer_name,
            buyer_email=invoice_data.buyer_email,
            buyer_phone=invoice_data.buyer_phone,
            invoice_description=invoice_data.invoice_description,
            activity=invoice_data.activity,
            amount=invoice_data.amount,
            currency=invoice_data.currency,
            status="PENDING",
            customer_reference=easykash_response.get("customer_reference"),
            easykash_reference=easykash_response.get("easykash_reference"),
        )

        db.add(new_invoice)
        db.commit()
        db.refresh(new_invoice)

        response_data = InvoiceCreateResponse(
            id=new_invoice.id,
            user_id=new_invoice.user_id,
            status=new_invoice.status,
            customer_reference=new_invoice.customer_reference,
            pay_url=easykash_response.get("pay_url"),
            created_at=new_invoice.created_at,
        )
        return response_data

    @staticmethod
    def get_invoice(db: Session, invoice_id: int, user_id: int) -> InvoiceResponse:
        """
        1. Retrieves a specific invoice for a given user from the database.
           (SECURITY: Ensures a user can only access their own invoice).
        2. Inquires its latest status from EasyKash.
        3. Updates the status in the database if it has changed.
        4. Returns the full invoice details.
        """
        # Step 1: Get the invoice from DB, ensuring it belongs to the user
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.user_id == user_id)
            .first()
        )
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )

        if not invoice.customer_reference:
            # This invoice was likely created before a payment link was generated.
            # Return it as is, without checking EasyKash.
            return invoice

        # Step 2: Inquire payment status from EasyKash
        inquiry_response = easykash_client.inquire_payment(invoice.customer_reference)

        if inquiry_response.get("error"):
            print(
                f"Could not inquire payment status for invoice {invoice.id}: {inquiry_response.get('details')}"
            )
            return invoice

        # Step 3: Update local status if necessary
        easykash_status = inquiry_response.get("status")
        easykash_ref = inquiry_response.get("easykashReference")

        needs_commit = False
        if easykash_status and easykash_status.upper() != invoice.status:
            invoice.status = easykash_status.upper()
            needs_commit = True

        if easykash_ref and easykash_ref != invoice.easykash_reference:
            invoice.easykash_reference = easykash_ref
            needs_commit = True

        if needs_commit:
            db.commit()
            db.refresh(invoice)

        # Step 4: Return the (potentially updated) invoice
        return invoice

    @staticmethod
    def get_invoice_admin(db: Session, invoice_id: int) -> InvoiceResponse:
        """
        1. Retrieves a specific invoice for a given user from the database.
           (SECURITY: Ensures a user can only access their own invoice).
        2. Inquires its latest status from EasyKash.
        3. Updates the status in the database if it has changed.
        4. Returns the full invoice details.
        """
        # Step 1: Get the invoice from DB, ensuring it belongs to the user
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )

        if not invoice.customer_reference:
            # This invoice was likely created before a payment link was generated.
            # Return it as is, without checking EasyKash.
            return invoice

        # Step 2: Inquire payment status from EasyKash
        inquiry_response = easykash_client.inquire_payment(invoice.customer_reference)

        if inquiry_response.get("error"):
            print(
                f"Could not inquire payment status for invoice {invoice.id}: {inquiry_response.get('details')}"
            )
            return invoice

        # Step 3: Update local status if necessary
        easykash_status = inquiry_response.get("status")
        easykash_ref = inquiry_response.get("easykashReference")

        needs_commit = False
        if easykash_status and easykash_status.upper() != invoice.status:
            invoice.status = easykash_status.upper()
            needs_commit = True

        if easykash_ref and easykash_ref != invoice.easykash_reference:
            invoice.easykash_reference = easykash_ref
            needs_commit = True

        if needs_commit:
            db.commit()
            db.refresh(invoice)

        # Step 4: Return the (potentially updated) invoice
        return invoice

    @staticmethod
    def get_my_invoices_for_user(db: Session, user_id: int) -> List[InvoiceResponse]:
        """
        Retrieves all invoices belonging to a specific user, ordered by creation date.
        """
        invoices = (
            db.query(Invoice)
            .filter(Invoice.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .all()
        )
        return invoices

    @staticmethod
    def get_all_invoices_for_admin(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[InvoiceResponse]:
        """
        Retrieves a paginated list of all invoices. (Admin only)
        """
        invoices = (
            db.query(Invoice)
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return invoices

    @staticmethod
    def get_invoices_summary_for_admin(db: Session) -> InvoiceSummaryResponse:
        """
        Calculates and returns a summary of all invoices. (Admin only)
        """
        total_invoices = db.query(Invoice).count()

        # Calculate total revenue only from PAID invoices
        total_revenue = (
            db.query(func.sum(Invoice.amount)).filter(Invoice.status == "PAID").scalar()
        ) or 0.0

        pending_count = db.query(Invoice).filter(Invoice.status == "PENDING").count()
        paid_count = db.query(Invoice).filter(Invoice.status == "PAID").count()

        # Consider multiple forms of failure states
        failed_statuses = ["FAILED", "CANCELLED", "EXPIRED"]
        failed_count = (
            db.query(Invoice).filter(Invoice.status.in_(failed_statuses)).count()
        )

        return InvoiceSummaryResponse(
            total_invoices=total_invoices,
            total_revenue=round(total_revenue, 2),
            pending_count=pending_count,
            paid_count=paid_count,
            failed_count=failed_count,
        )

    @staticmethod
    def get_all_invoices_for_admin(
        db: Session, skip: int = 0, limit: int = 100, search: str = None
    ) -> List[InvoiceResponse]:
        """
        Retrieves a paginated list of all invoices. (Admin only)
        Can be filtered by a search term on customer_reference.
        """
        query = db.query(Invoice)

        # [NEW] Add search filter if a search term is provided
        if search:
            # Use ilike for case-insensitive partial matching
            query = query.filter(Invoice.customer_reference.ilike(f"%{search}%"))

        invoices = (
            query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
        )
        return invoices
