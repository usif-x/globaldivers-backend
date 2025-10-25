# app/services/invoice_service.py

from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.mailer import send_email
from app.core.telegram import notify_admins
from app.models.invoice import Invoice

# --- IMPORT THE NEW SCHEMA ---
from app.schemas.invoice import UserInvoiceSummaryResponse  # <-- NEW
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceCreateResponse,
    InvoiceResponse,
    InvoiceSummaryResponse,
    InvoiceUpdate,
)
from app.utils.easykash import easykash_client


class InvoiceService:
    @staticmethod
    def create_invoice(
        db: Session, invoice_data: InvoiceCreate, user_id: int
    ) -> InvoiceCreateResponse:
        # Validate invoice_type
        if invoice_data.invoice_type not in ["online", "cash"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice type must be either 'online' or 'cash'",
            )

        # Convert activity_details to a list of dicts for database storage
        activity_details_dict = (
            [
                details.model_dump(mode="json")
                for details in invoice_data.activity_details
            ]
            if invoice_data.activity_details
            else None
        )

        # Initialize common invoice data
        customer_reference = None
        pay_url = None
        easykash_reference = None
        status = "PENDING"

        # Handle online payments
        if invoice_data.invoice_type == "online":
            payment_payload = invoice_data.model_dump()
            easykash_response = easykash_client.create_payment(
                payment_data=payment_payload, user_id=user_id
            )

            if not easykash_response.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create payment link: {easykash_response.get('details')}",
                )

            customer_reference = easykash_response.get("customer_reference")
            pay_url = easykash_response.get("pay_url")
            easykash_reference = easykash_response.get("easykash_reference")
        else:
            # For cash payments, generate a simple customer reference for tracking
            import random

            customer_reference = (
                f"{random.randint(1000, 9999)}{user_id}{random.randint(1000,9999)}"
            )

        new_invoice = Invoice(
            user_id=user_id,
            buyer_name=invoice_data.buyer_name,
            buyer_email=invoice_data.buyer_email,
            buyer_phone=invoice_data.buyer_phone,
            invoice_description=invoice_data.invoice_description,
            activity=invoice_data.activity,
            activity_details=activity_details_dict,
            amount=invoice_data.amount,
            currency=invoice_data.currency,
            invoice_type=invoice_data.invoice_type,
            pay_url=pay_url,
            status=status,
            picked_up=False,
            customer_reference=customer_reference,
            easykash_reference=easykash_reference,
        )

        db.add(new_invoice)
        db.commit()
        db.refresh(new_invoice)

        # --- Enhanced Telegram Notification ---
        activity_details_str = ""
        if new_invoice.activity_details:
            for detail in new_invoice.activity_details:
                activity_details_str += (
                    f"  - <b>{detail.get('name', 'N/A')}</b>\n"
                    f"    <b>Date:</b> {detail.get('activity_date', 'N/A')}\n"
                    f"    <b>Guests:</b> {detail.get('adults', 0)} Adult(s), {detail.get('children', 0)} Child(ren)\n"
                    f"    <b>Hotel:</b> {detail.get('hotel_name', 'N/A')}, Room #{detail.get('room_number', 'N/A')}\n"
                    f"    <b>Requests:</b> {detail.get('special_requests', 'None')}\n\n"
                )

        message = (
            "<b>🧾 New Invoice Created</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>🆔 ID:</b> <code>{new_invoice.id}</code>\n"
            f"<b>👤 User ID:</b> <code>{new_invoice.user_id}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>🛍️ Buyer:</b> {new_invoice.buyer_name}\n"
            f"<b>📧 Email:</b> {new_invoice.buyer_email}\n"
            f"<b>📞 Phone:</b> {new_invoice.buyer_phone}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>📝 Description:</b> {new_invoice.invoice_description}\n"
            f"<b>🏷️ Activity:</b> {new_invoice.activity}\n"
            f"<b>💳 Type:</b> {new_invoice.invoice_type.upper()}\n\n"
            f"<b>📋 Activity Details:</b>\n{activity_details_str if activity_details_str else '  None provided.'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>💰 Amount:</b> <code>{new_invoice.amount} {new_invoice.currency}</code>\n"
            f"<b>📊 Status:</b> <b>{new_invoice.status}</b>\n\n"
        )

        if new_invoice.invoice_type == "online":
            message += (
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>🧾 Customer Reference:</b> <code>{new_invoice.customer_reference}</code>\n"
                f"<b>🔢 EasyKash Reference:</b> <code>{new_invoice.easykash_reference}</code>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>🔗 Pay URL:</b> <a href='{new_invoice.pay_url}'>Click to Pay</a>\n\n"
            )
        else:
            message += (
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>🧾 Customer Reference:</b> <code>{new_invoice.customer_reference}</code>\n"
                "<b>💵 CASH PAYMENT</b> - No online payment required\n\n"
            )

        message += f"<b>📅 Created At:</b> {new_invoice.created_at}"

        notify_admins(message)

        # Send invoice creation email to customer
        try:
            if invoice_data.invoice_type == "online":
                payment_section = f"""
                <div class="button-container">
                  <a href="{new_invoice.pay_url}" class="button">Pay Now Online</a>
                </div>
                <div class="note">
                  ⏰ Please complete your payment to secure your booking.
                </div>
                """
            else:
                payment_section = """
                <div class="note">
                  💵 <strong>Cash Payment:</strong> You can pay in cash when you arrive. 
                  Please keep your reference number for verification.
                </div>
                """

            send_email(
                to_email=new_invoice.buyer_email,
                subject=f"Invoice Created - {new_invoice.activity}",
                template_name="invoice_created.html",
                context={
                    "buyer_name": new_invoice.buyer_name,
                    "invoice_id": str(new_invoice.id),
                    "customer_reference": new_invoice.customer_reference,
                    "activity": new_invoice.activity,
                    "description": new_invoice.invoice_description,
                    "amount": str(new_invoice.amount),
                    "currency": new_invoice.currency,
                    "payment_section": payment_section,
                },
            )
        except Exception as e:
            # Log the error but don't fail the invoice creation
            print(f"Failed to send invoice creation email: {e}")

        response_data = InvoiceCreateResponse(
            id=new_invoice.id,
            user_id=new_invoice.user_id,
            status=new_invoice.status,
            customer_reference=new_invoice.customer_reference,
            pay_url=new_invoice.pay_url,
            invoice_type=new_invoice.invoice_type,
            created_at=new_invoice.created_at,
        )
        return response_data

    @staticmethod
    def _inquire_and_update_invoice(db: Session, invoice: Invoice) -> Invoice:
        """
        A private helper to check an invoice's status and only inquire with
        EasyKash if the status is not already in a final state.
        This prevents unnecessary API calls.
        """
        # Define statuses that are considered final and won't change.
        FINAL_STATUSES = {"PAID", "EXPIRED", "CANCELLED"}

        # 1. OPTIMIZATION: If status is final or we can't inquire, return immediately.
        if invoice.status in FINAL_STATUSES or not invoice.customer_reference:
            print(
                f"Skipping API inquiry for invoice {invoice.id} (status: {invoice.status})."
            )
            return invoice

        # 2. If status is not final (e.g., PENDING), inquire for the latest update.
        print(f"Inquiring status for invoice {invoice.id} (status: {invoice.status}).")
        inquiry_response = easykash_client.inquire_payment(invoice.customer_reference)

        if inquiry_response.get("error"):
            print(
                f"Could not inquire payment status for invoice {invoice.id}: {inquiry_response.get('details')}"
            )
            # Return the invoice as-is if the API call fails
            return invoice

        # 3. Process the response and update the database if the status has changed.
        easykash_status_str = inquiry_response.get("status")
        easykash_ref = inquiry_response.get("easykashReference")

        # Ensure we have a status string to work with
        easykash_status = easykash_status_str.upper() if easykash_status_str else None

        needs_commit = False
        if easykash_status and easykash_status != invoice.status:
            invoice.status = easykash_status
            needs_commit = True

        if easykash_ref and easykash_ref != invoice.easykash_reference:
            invoice.easykash_reference = easykash_ref
            needs_commit = True

        if needs_commit:
            db.commit()
            db.refresh(invoice)
            print(f"Updated invoice {invoice.id} status to {invoice.status}.")

        return invoice

    # --- UPDATED: User-facing get_invoice method ---
    @staticmethod
    def get_invoice(db: Session, invoice_id: int, user_id: int) -> InvoiceResponse:
        """
        Retrieves a specific invoice for a user.
        It will only check for status updates with the payment provider if the
        invoice is not already in a final state (e.g., PAID, EXPIRED).
        """
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.user_id == user_id)
            .first()
        )
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )

        # Call the shared helper to handle the inquiry logic
        return InvoiceService._inquire_and_update_invoice(db, invoice)

    # --- UPDATED: Admin-facing get_invoice_admin method ---
    @staticmethod
    def get_invoice_admin(db: Session, invoice_id: int) -> InvoiceResponse:
        """
        Retrieves any specific invoice for an admin.
        It will only check for status updates with the payment provider if the
        invoice is not already in a final state (e.g., PAID, EXPIRED).
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )

        # Call the same shared helper to handle the inquiry logic
        return InvoiceService._inquire_and_update_invoice(db, invoice)

    @staticmethod
    def get_my_invoices_for_user(db: Session, user_id: int) -> List[InvoiceResponse]:
        invoices = (
            db.query(Invoice)
            .filter(Invoice.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .all()
        )
        return invoices

    # --- ENHANCED Admin Summary ---
    @staticmethod
    def get_invoices_summary_for_admin(db: Session) -> InvoiceSummaryResponse:
        """
        Calculates and returns a detailed summary of all invoices. (Admin only)
        """
        failed_statuses = ["FAILED", "CANCELLED", "EXPIRED"]

        paid_query = (
            db.query(func.count(Invoice.id), func.sum(Invoice.amount))
            .filter(Invoice.status == "PAID")
            .one()
        )

        pending_query = (
            db.query(func.count(Invoice.id), func.sum(Invoice.amount))
            .filter(Invoice.status == "PENDING")
            .one()
        )

        failed_query = (
            db.query(func.count(Invoice.id), func.sum(Invoice.amount))
            .filter(Invoice.status.in_(failed_statuses))
            .one()
        )

        paid_count, total_revenue = paid_query
        pending_count, pending_amount_total = pending_query
        failed_count, failed_amount_total = failed_query

        total_invoices = (paid_count or 0) + (pending_count or 0) + (failed_count or 0)

        return InvoiceSummaryResponse(
            total_invoices=total_invoices,
            total_revenue=round(total_revenue or 0.0, 2),
            pending_count=pending_count or 0,
            pending_amount_total=round(pending_amount_total or 0.0, 2),
            paid_count=paid_count or 0,
            failed_count=failed_count or 0,
            failed_amount_total=round(failed_amount_total or 0.0, 2),
        )

    # --- NEW User Summary Method ---
    @staticmethod
    def get_summary_for_user(db: Session, user_id: int) -> UserInvoiceSummaryResponse:
        """
        Calculates and returns a detailed summary of invoices for a specific user.
        """
        failed_statuses = ["FAILED", "CANCELLED", "EXPIRED"]

        # Paid invoices: count and total amount
        paid_count, paid_amount = (
            db.query(func.count(Invoice.id), func.sum(Invoice.amount))
            .filter(Invoice.user_id == user_id, Invoice.status == "PAID")
            .one()
        )

        # Pending invoices: count and total amount
        pending_count, pending_amount = (
            db.query(func.count(Invoice.id), func.sum(Invoice.amount))
            .filter(Invoice.user_id == user_id, Invoice.status == "PENDING")
            .one()
        )

        # Failed invoices: count and total amount
        failed_count, failed_amount = (
            db.query(func.count(Invoice.id), func.sum(Invoice.amount))
            .filter(Invoice.user_id == user_id, Invoice.status.in_(failed_statuses))
            .one()
        )

        total_invoices = (paid_count or 0) + (pending_count or 0) + (failed_count or 0)

        return UserInvoiceSummaryResponse(
            total_invoices=total_invoices,
            paid_invoices_count=paid_count or 0,
            paid_amount_total=round(paid_amount or 0.0, 2),
            pending_invoices_count=pending_count or 0,
            pending_amount_total=round(pending_amount or 0.0, 2),
            failed_invoices_count=failed_count or 0,
            failed_amount_total=round(failed_amount or 0.0, 2),
        )

    @staticmethod
    def get_last_invoice_for_user(db: Session, user_id: int) -> InvoiceResponse:
        """
        Retrieves the most recently created invoice for a specific user.
        Raises a 404 error if the user has no invoices.
        Also, inquires for the latest status if the invoice is not in a final state.
        """
        # 1. Query the database for the user's invoices, order by creation date descending, and get the first one.
        invoice = (
            db.query(Invoice)
            .filter(Invoice.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No invoices found for this user.",
            )

        # 2. Reuse our existing helper to efficiently get the latest status.
        return InvoiceService._inquire_and_update_invoice(db, invoice)

    @staticmethod
    def get_invoice_by_reference_for_user(
        db: Session, customer_reference: str, user_id: int
    ) -> InvoiceResponse:
        """
        Retrieves a specific invoice by its customer_reference, but only if it
        belongs to the specified user. This is a critical security check.
        """
        # 1. Query by both reference and user_id to ensure ownership.
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.customer_reference == customer_reference,
                Invoice.user_id == user_id,
            )
            .first()
        )

        if not invoice:
            # Return a 404. We don't want to tell a potential attacker
            # that the invoice exists but belongs to someone else.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found or you do not have permission to view it.",
            )

        # 2. If found, get the latest status before returning.
        return InvoiceService._inquire_and_update_invoice(db, invoice)

    # --- CLEANUP: Removed duplicated function, keeping the one with search ---
    @staticmethod
    def get_all_invoices_for_admin(
        db: Session, skip: int = 0, limit: int = 100, search: str = None
    ) -> List[InvoiceResponse]:
        """
        Retrieves a paginated list of all invoices. (Admin only)
        Can be filtered by a search term on customer_reference.
        """
        query = db.query(Invoice)

        if search:
            query = query.filter(Invoice.customer_reference.ilike(f"%{search}%"))

        invoices = (
            query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
        )
        return invoices

    @staticmethod
    def update_invoice_admin(
        db: Session, invoice_id: int, invoice_data: InvoiceUpdate
    ) -> InvoiceResponse:
        """
        Updates an invoice's details. (Admin only)
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )

        # Get the update data, excluding any fields that were not sent
        update_data = invoice_data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided",
            )

        for key, value in update_data.items():
            if key == "activity_details" and value:
                # Pydantic models in a list need to be converted to dicts
                setattr(invoice, key, [item.model_dump(mode="json") for item in value])
            else:
                setattr(invoice, key, value)

        db.commit()
        db.refresh(invoice)
        return invoice

    def update_invoice_picked_up_status(db: Session, invoice_id: int, picked_up: bool):
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )
        invoice.picked_up = picked_up
        db.commit()
        db.refresh(invoice)
        return {"message": "Invoice picked up status updated"}

    # --- NEW Admin Delete Method ---
    @staticmethod
    def delete_invoice_admin(db: Session, invoice_id: int):
        """
        Deletes an invoice permanently from the database. (Admin only)
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )

        db.delete(invoice)
        db.commit()
        return {"message": "Invoice deleted"}

    @staticmethod
    def process_payment_callback(db: Session, payload: dict):
        """
        Updates an invoice based on a verified payment callback.
        """
        # --- 1. Find invoice ---
        invoice = (
            db.query(Invoice)
            .filter(Invoice.customer_reference == payload.get("customerReference"))
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with customer reference {payload.get('customerReference')} not found.",
            )

        # --- 2. Idempotency ---
        if invoice.status == "PAID":
            return {"status": "success", "message": "Invoice already marked as paid."}

        # --- 3. Validate status ---
        incoming_status = payload.get("status", "").upper()
        VALID_CALLBACK_STATUSES = ["PAID", "FAILED", "CANCELLED", "EXPIRED"]

        if incoming_status not in VALID_CALLBACK_STATUSES:
            print(
                f"Received unknown status '{payload.get('status')}' "
                f"for invoice ref {payload.get('customerReference')}."
            )
            return {
                "status": "noop",
                "message": f"Received unhandled status '{payload.get('status')}'. Invoice not updated.",
            }

        # --- 4. Update invoice ---
        invoice.status = incoming_status
        invoice.easykash_reference = payload.get("easykashRef")
        invoice.payment_method = payload.get("paymentMethod")

        db.commit()
        db.refresh(invoice)

        # Send payment success email if payment is confirmed
        if incoming_status == "PAID":
            try:
                send_email(
                    to_email=invoice.buyer_email,
                    subject=f"Payment Confirmed - {invoice.activity}",
                    template_name="payment_success.html",
                    context={
                        "buyer_name": invoice.buyer_name,
                        "invoice_id": str(invoice.id),
                        "customer_reference": invoice.customer_reference,
                        "activity": invoice.activity,
                        "payment_method": invoice.payment_method or "Online Payment",
                        "amount": str(invoice.amount),
                        "currency": invoice.currency,
                    },
                )
            except Exception as e:
                # Log the error but don't fail the callback processing
                print(f"Failed to send payment success email: {e}")

        return {
            "status": "success",
            "message": f"Invoice updated to {incoming_status}.",
        }
