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
    InvoiceActivityBreakdown,
    InvoiceCreate,
    InvoiceCreateResponse,
    InvoiceDetailedSummaryResponse,
    InvoicePaymentMethodBreakdown,
    InvoiceResponse,
    InvoiceSummaryResponse,
    InvoiceTypeBreakdown,
    InvoiceUpdate,
    MonthlyInvoiceAnalytics,
    TopCustomerResponse,
)
from app.services.activity_availability import ActivityAvailabilityService
from app.services.coupon import CouponServices
from app.services.price_calculator import PriceCalculator
from app.utils.currency_converter import CurrencyConverter
from app.utils.easykash import easykash_client


class InvoiceService:
    @staticmethod
    def create_invoice(
        db: Session, invoice_data: InvoiceCreate, user_id: int
    ) -> InvoiceCreateResponse:
        """
        Create a new invoice with backend-validated pricing.

        This method:
        1. Validates the activity type
        2. Calculates the correct price based on activity details
        3. Verifies the submitted amount matches the calculated amount
        4. Applies all applicable discounts (group, promo)
        5. Creates the invoice with payment processing if online

        Args:
            db: Database session
            invoice_data: Invoice creation data with user inputs
            user_id: ID of the user creating the invoice

        Returns:
            InvoiceCreateResponse with invoice details and discount breakdown

        Raises:
            HTTPException: If validation fails or pricing doesn't match
        """

        # Step 1: Validate invoice_type
        if invoice_data.invoice_type not in ["online", "cash"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice type must be either 'online' or 'cash'",
            )

        # Step 2: Validate activity type and calculate the correct price
        activity = invoice_data.activity.lower()
        calculated_amount = None
        discount_amount = 0.0
        discount_breakdown = None
        coupon_obj = None

        if activity == "trip":
            # Trip activity requires trip_id and participant details
            if not invoice_data.trip_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="trip_id is required when activity type is 'trip'",
                )

            if invoice_data.adults is None or invoice_data.adults < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least 1 adult is required for trip bookings",
                )

            # --- AVAILABILITY CHECK ---
            # Check if trip is available on all requested dates
            if invoice_data.activity_details:
                for detail in invoice_data.activity_details:
                    if hasattr(detail, "activity_date") and detail.activity_date:
                        availability = ActivityAvailabilityService.check_availability(
                            db=db,
                            activity_type="trip",
                            activity_id=invoice_data.trip_id,
                            target_date=detail.activity_date,
                        )
                        if not availability.is_available:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Trip is not available on {detail.activity_date}. Reason: {availability.reason or 'Closed for booking'}",
                            )

            children = invoice_data.children if invoice_data.children else 0

            # Calculate price using PriceCalculator
            try:
                (
                    calculated_amount,
                    discount_amount,
                    discount_breakdown,
                    coupon_obj,
                ) = PriceCalculator.calculate_trip_price(
                    db=db,
                    trip_id=invoice_data.trip_id,
                    adults=invoice_data.adults,
                    children=children,
                    coupon_code=invoice_data.coupon_code,
                    user_id=user_id,
                )
            except HTTPException:
                raise

        elif activity == "course":
            # Course activity requires course_id
            if not invoice_data.course_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="course_id is required when activity type is 'course'",
                )

            # --- AVAILABILITY CHECK ---
            # Check if course is available on all requested dates
            if invoice_data.activity_details:
                for detail in invoice_data.activity_details:
                    if hasattr(detail, "activity_date") and detail.activity_date:
                        availability = ActivityAvailabilityService.check_availability(
                            db=db,
                            activity_type="course",
                            activity_id=invoice_data.course_id,
                            target_date=detail.activity_date,
                        )
                        if not availability.is_available:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Course is not available on {detail.activity_date}. Reason: {availability.reason or 'Closed for booking'}",
                            )

            # Calculate price using PriceCalculator
            try:
                (
                    calculated_amount,
                    discount_amount,
                    discount_breakdown,
                    coupon_obj,
                ) = PriceCalculator.calculate_course_price(
                    db=db,
                    course_id=invoice_data.course_id,
                    coupon_code=invoice_data.coupon_code,
                    user_id=user_id,
                )
            except HTTPException:
                raise

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported activity type: '{activity}'. Must be 'trip' or 'course'",
            )

        # Step 3: Verify that the submitted amount matches the calculated amount
        # For non-EGP currencies, convert the calculated EGP amount to target currency for verification
        verification_amount = calculated_amount
        if invoice_data.currency != "EGP":
            converted_for_verification = CurrencyConverter.convert_amount_sync(
                from_currency="EGP",
                to_currency=invoice_data.currency,
                amount=calculated_amount,
            )
            if converted_for_verification is not None:
                verification_amount = converted_for_verification
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Currency conversion from EGP to {invoice_data.currency} failed during verification",
                )

        if not PriceCalculator.verify_amount_matches_calculation(
            verification_amount, invoice_data.amount, tolerance=1.0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount mismatch detected. Expected: {verification_amount}, Got: {invoice_data.amount}. "
                f"Please recalculate your booking.",
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
        invoice_status = "PENDING"

        # Step 4: Handle online payments
        final_amount = calculated_amount

        if invoice_data.invoice_type == "online":
            # Convert amount to target currency if not EGP
            payment_amount = final_amount
            if invoice_data.currency != "EGP":
                converted_amount = CurrencyConverter.convert_amount_sync(
                    from_currency="EGP",
                    to_currency=invoice_data.currency,
                    amount=final_amount,
                )
                if converted_amount is not None:
                    payment_amount = converted_amount
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Currency conversion from EGP to {invoice_data.currency} failed",
                    )
            else:
                # For EGP, maintain full precision
                payment_amount = final_amount

            payment_payload = invoice_data.model_dump()
            # Update amount in payload to the payment amount in target currency
            payment_payload["amount"] = payment_amount

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
            # For cash payments, use EGP amount
            payment_amount = final_amount
            # Generate a simple customer reference for tracking
            import random

            customer_reference = (
                f"{random.randint(1000, 9999)}{user_id}{random.randint(1000,9999)}"
            )

        # Step 5: Create the invoice record
        new_invoice = Invoice(
            user_id=user_id,
            buyer_name=invoice_data.buyer_name,
            buyer_email=invoice_data.buyer_email,
            buyer_phone=invoice_data.buyer_phone,
            invoice_description=invoice_data.invoice_description,
            activity=invoice_data.activity,
            activity_details=activity_details_dict,
            amount=payment_amount,  # Use payment amount in target currency
            currency=invoice_data.currency,
            invoice_type=invoice_data.invoice_type,
            pay_url=pay_url,
            status=invoice_status,
            picked_up=False,
            customer_reference=customer_reference,
            easykash_reference=easykash_reference,
            coupon_code=invoice_data.coupon_code,
            discount_amount=discount_amount,
            discount_breakdown=discount_breakdown,
        )

        db.add(new_invoice)
        db.commit()
        db.refresh(new_invoice)

        # Step 6: Consume the coupon if one was used
        if coupon_obj and invoice_data.coupon_code:
            coupon_service = CouponServices(db)
            coupon_service.consume_coupon(invoice_data.coupon_code, user_id)

        # Step 7: Enhanced Telegram Notification
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

        coupon_str = ""
        if new_invoice.coupon_code and discount_breakdown:
            coupon_str = f"<b>🏷️ Coupon:</b> {new_invoice.coupon_code} (Saved {new_invoice.discount_amount})\n"

        # Add discount breakdown to message if available
        discount_detail_str = ""
        if discount_breakdown:
            discount_detail_str += (
                f"<b>💵 Base Price:</b> {discount_breakdown.get('base_price', 0)}\n"
            )
            if discount_breakdown.get("group_discount"):
                gd = discount_breakdown["group_discount"]
                discount_detail_str += f"<b>👥 Group Discount:</b> -{gd.get('amount', 0)} ({gd.get('percentage', 0)}%)\n"
            if discount_breakdown.get("promo_discount"):
                pd = discount_breakdown["promo_discount"]
                discount_detail_str += f"<b>🎟️ Promo Discount:</b> -{pd.get('amount', 0)} ({pd.get('percentage', 0)}%)\n"
            discount_detail_str += (
                f"<b>💰 Final Price:</b> {discount_breakdown.get('final_price', 0)}\n\n"
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
            f"{discount_detail_str}"
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

        response_data = InvoiceCreateResponse(
            id=new_invoice.id,
            user_id=new_invoice.user_id,
            status=new_invoice.status,
            customer_reference=new_invoice.customer_reference,
            pay_url=new_invoice.pay_url,
            invoice_type=new_invoice.invoice_type,
            created_at=new_invoice.created_at,
            discount_breakdown=discount_breakdown,
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

    @staticmethod
    def get_invoice_by_reference_public(
        db: Session, customer_reference: str
    ) -> InvoiceResponse:
        """
        Public method to retrieve an invoice by its customer_reference.
        No authentication required - used for fast status checks.
        """
        invoice = (
            db.query(Invoice)
            .filter(Invoice.customer_reference == customer_reference)
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )

        # Get the latest status before returning
        return InvoiceService._inquire_and_update_invoice(db, invoice)

    @staticmethod
    def update_pickup_status_public(
        db: Session, customer_reference: str, picked_up: bool
    ) -> InvoiceResponse:
        """
        Public method to update invoice pickup status using customer_reference.
        No authentication required - used for fast pickup updates.
        """
        invoice = (
            db.query(Invoice)
            .filter(Invoice.customer_reference == customer_reference)
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )

        invoice.picked_up = picked_up
        db.commit()
        db.refresh(invoice)

        # Get the latest status before returning
        return InvoiceService._inquire_and_update_invoice(db, invoice)

    @staticmethod
    def update_payment_status_public(
        db: Session, customer_reference: str, payment_status: str
    ) -> InvoiceResponse:
        """
        Public method to update invoice payment status using customer_reference.
        No authentication required - used for fast payment status updates.

        Args:
            db: Database session
            customer_reference: Invoice reference number
            payment_status: New status (PAID, PENDING, CANCELLED, EXPIRED, FAILED)

        Returns:
            Updated invoice

        Raises:
            HTTPException: If invoice not found
        """
        invoice = (
            db.query(Invoice)
            .filter(Invoice.customer_reference == customer_reference)
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )

        # Update the status
        invoice.status = payment_status
        db.commit()
        db.refresh(invoice)

        # Send Telegram notification about status change
        message = (
            f"<b>💳 Invoice Payment Status Updated</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>🆔 Invoice ID:</b> <code>{invoice.id}</code>\n"
            f"<b>📝 Reference:</b> <code>{invoice.customer_reference}</code>\n"
            f"<b>👤 User:</b> {invoice.buyer_name}\n"
            f"<b>💰 Amount:</b> {invoice.amount} {invoice.currency}\n"
            f"<b>📊 New Status:</b> <b>{payment_status}</b>\n"
            f"<b>🕐 Updated At:</b> {invoice.updated_at}"
        )
        notify_admins(message)

        return invoice

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
            # try:
            #     send_email(
            #         to_email=invoice.buyer_email,
            #         subject=f"Payment Confirmed - {invoice.activity}",
            #         template_name="payment_success.html",
            #         context={
            #             "buyer_name": invoice.buyer_name,
            #             "invoice_id": str(invoice.id),
            #             "customer_reference": invoice.customer_reference,
            #             "activity": invoice.activity,
            #             "payment_method": invoice.payment_method or "Online Payment",
            #             "amount": str(invoice.amount),
            #             "currency": invoice.currency,
            #         },
            #     )
            # except Exception as e:
            #     # Log the error but don't fail the callback processing
            #     print(f"Failed to send payment success email: {e}")

            return {
                "status": "success",
                "message": f"Invoice updated to {incoming_status}.",
            }

    # --- NEW: Enhanced Analytics Methods ---

    @staticmethod
    def get_detailed_summary_for_admin(db: Session) -> InvoiceDetailedSummaryResponse:
        """
        Get comprehensive invoice analytics with breakdowns.
        """
        from datetime import datetime

        from sqlalchemy import case

        # Basic counts
        total_invoices = db.query(Invoice).count()
        confirmed_invoices = (
            db.query(Invoice).filter(Invoice.is_confirmed == True).count()
        )
        unconfirmed_invoices = total_invoices - confirmed_invoices

        # Status breakdown
        paid_count = db.query(Invoice).filter(Invoice.status == "PAID").count()
        pending_count = db.query(Invoice).filter(Invoice.status == "PENDING").count()
        failed_count = db.query(Invoice).filter(Invoice.status == "FAILED").count()
        cancelled_count = (
            db.query(Invoice).filter(Invoice.status == "CANCELLED").count()
        )
        expired_count = db.query(Invoice).filter(Invoice.status == "EXPIRED").count()

        # Revenue metrics
        total_revenue = (
            db.query(func.sum(Invoice.amount)).filter(Invoice.status == "PAID").scalar()
            or 0.0
        )
        pending_amount = (
            db.query(func.sum(Invoice.amount))
            .filter(Invoice.status == "PENDING")
            .scalar()
            or 0.0
        )
        failed_amount = (
            db.query(func.sum(Invoice.amount))
            .filter(Invoice.status.in_(["FAILED", "CANCELLED", "EXPIRED"]))
            .scalar()
            or 0.0
        )

        average_invoice_amount = db.query(func.avg(Invoice.amount)).scalar() or 0.0

        # Conversion metrics
        conversion_rate = (
            (paid_count / total_invoices * 100) if total_invoices > 0 else 0.0
        )
        payment_attempts = paid_count + failed_count + cancelled_count + expired_count
        payment_success_rate = (
            (paid_count / payment_attempts * 100) if payment_attempts > 0 else 0.0
        )

        # Activity breakdown
        activity_name_expr = func.coalesce(
            Invoice.activity_details[0]["name"].astext,
            Invoice.activity_details[0]["activity_name"].astext,
            func.initcap(Invoice.activity),
        )

        activity_stats = (
            db.query(
                activity_name_expr.label("activity"),
                func.count(Invoice.id).label("count"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_revenue"),
                func.avg(Invoice.amount).label("average_amount"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_count"
                ),
                func.sum(case((Invoice.status == "PENDING", 1), else_=0)).label(
                    "pending_count"
                ),
                func.sum(
                    case(
                        (Invoice.status.in_(["FAILED", "CANCELLED", "EXPIRED"]), 1),
                        else_=0,
                    )
                ).label("failed_count"),
            )
            .group_by(activity_name_expr)
            .all()
        )

        activity_breakdown = [
            InvoiceActivityBreakdown(
                activity=stat.activity,
                count=stat.count,
                total_revenue=float(stat.total_revenue or 0),
                average_amount=float(stat.average_amount or 0),
                paid_count=int(stat.paid_count or 0),
                pending_count=int(stat.pending_count or 0),
                failed_count=int(stat.failed_count or 0),
            )
            for stat in activity_stats
        ]

        # Payment method breakdown
        payment_stats = (
            db.query(
                Invoice.payment_method,
                func.count(Invoice.id).label("count"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_revenue"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_count"
                ),
            )
            .filter(Invoice.payment_method.isnot(None))
            .group_by(Invoice.payment_method)
            .all()
        )

        payment_method_breakdown = [
            InvoicePaymentMethodBreakdown(
                payment_method=stat.payment_method,
                count=stat.count,
                total_revenue=float(stat.total_revenue or 0),
                success_rate=(
                    (stat.paid_count / stat.count * 100) if stat.count > 0 else 0.0
                ),
            )
            for stat in payment_stats
        ]

        # Invoice type breakdown
        type_stats = (
            db.query(
                Invoice.invoice_type,
                func.count(Invoice.id).label("count"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_revenue"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_count"
                ),
                func.sum(case((Invoice.status == "PENDING", 1), else_=0)).label(
                    "pending_count"
                ),
            )
            .group_by(Invoice.invoice_type)
            .all()
        )

        invoice_type_breakdown = [
            InvoiceTypeBreakdown(
                invoice_type=stat.invoice_type,
                count=stat.count,
                total_revenue=float(stat.total_revenue or 0),
                paid_count=int(stat.paid_count or 0),
                pending_count=int(stat.pending_count or 0),
            )
            for stat in type_stats
        ]

        # Pickup tracking
        picked_up_count = db.query(Invoice).filter(Invoice.picked_up == True).count()
        not_picked_up_count = (
            db.query(Invoice).filter(Invoice.picked_up == False).count()
        )

        return InvoiceDetailedSummaryResponse(
            total_invoices=total_invoices,
            confirmed_invoices=confirmed_invoices,
            unconfirmed_invoices=unconfirmed_invoices,
            paid_count=paid_count,
            pending_count=pending_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            expired_count=expired_count,
            total_revenue=round(total_revenue, 2),
            pending_amount=round(pending_amount, 2),
            failed_amount=round(failed_amount, 2),
            average_invoice_amount=round(average_invoice_amount, 2),
            conversion_rate=round(conversion_rate, 2),
            payment_success_rate=round(payment_success_rate, 2),
            activity_breakdown=activity_breakdown,
            payment_method_breakdown=payment_method_breakdown,
            invoice_type_breakdown=invoice_type_breakdown,
            picked_up_count=picked_up_count,
            not_picked_up_count=not_picked_up_count,
        )

    @staticmethod
    def get_monthly_analytics(
        db: Session, year: int, month: int
    ) -> MonthlyInvoiceAnalytics:
        """
        Get invoice analytics for a specific month.

        Args:
            db: Database session
            year: Year (e.g., 2025)
            month: Month number (1-12)
        """
        from datetime import datetime

        from sqlalchemy import case, extract

        # Filter invoices for the specified month
        invoices_query = db.query(Invoice).filter(
            extract("year", Invoice.created_at) == year,
            extract("month", Invoice.created_at) == month,
        )

        # Basic counts
        total_invoices = invoices_query.count()
        confirmed_invoices = invoices_query.filter(Invoice.is_confirmed == True).count()
        unconfirmed_invoices = total_invoices - confirmed_invoices

        # Status breakdown
        paid_count = invoices_query.filter(Invoice.status == "PAID").count()
        pending_count = invoices_query.filter(Invoice.status == "PENDING").count()
        failed_count = invoices_query.filter(
            Invoice.status.in_(["FAILED", "CANCELLED", "EXPIRED"])
        ).count()

        # Revenue
        total_revenue = (
            invoices_query.filter(Invoice.status == "PAID")
            .with_entities(func.sum(Invoice.amount))
            .scalar()
            or 0.0
        )

        pending_amount = (
            invoices_query.filter(Invoice.status == "PENDING")
            .with_entities(func.sum(Invoice.amount))
            .scalar()
            or 0.0
        )

        average_invoice_amount = (
            invoices_query.with_entities(func.avg(Invoice.amount)).scalar() or 0.0
        )

        # Conversion
        conversion_rate = (
            (paid_count / total_invoices * 100) if total_invoices > 0 else 0.0
        )

        # Activity breakdown
        activity_name_expr = func.coalesce(
            Invoice.activity_details[0]["name"].astext,
            Invoice.activity_details[0]["activity_name"].astext,
            func.initcap(Invoice.activity),
        )

        activity_stats = (
            db.query(
                activity_name_expr.label("activity"),
                func.count(Invoice.id).label("count"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_revenue"),
                func.avg(Invoice.amount).label("average_amount"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_count"
                ),
                func.sum(case((Invoice.status == "PENDING", 1), else_=0)).label(
                    "pending_count"
                ),
                func.sum(
                    case(
                        (Invoice.status.in_(["FAILED", "CANCELLED", "EXPIRED"]), 1),
                        else_=0,
                    )
                ).label("failed_count"),
            )
            .filter(
                extract("year", Invoice.created_at) == year,
                extract("month", Invoice.created_at) == month,
            )
            .group_by(activity_name_expr)
            .all()
        )

        activity_breakdown = [
            InvoiceActivityBreakdown(
                activity=stat.activity,
                count=stat.count,
                total_revenue=float(stat.total_revenue or 0),
                average_amount=float(stat.average_amount or 0),
                paid_count=int(stat.paid_count or 0),
                pending_count=int(stat.pending_count or 0),
                failed_count=int(stat.failed_count or 0),
            )
            for stat in activity_stats
        ]

        # Payment method breakdown
        payment_stats = (
            db.query(
                Invoice.payment_method,
                func.count(Invoice.id).label("count"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_revenue"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_count"
                ),
            )
            .filter(
                Invoice.payment_method.isnot(None),
                extract("year", Invoice.created_at) == year,
                extract("month", Invoice.created_at) == month,
            )
            .group_by(Invoice.payment_method)
            .all()
        )

        payment_method_breakdown = [
            InvoicePaymentMethodBreakdown(
                payment_method=stat.payment_method,
                count=stat.count,
                total_revenue=float(stat.total_revenue or 0),
                success_rate=(
                    (stat.paid_count / stat.count * 100) if stat.count > 0 else 0.0
                ),
            )
            for stat in payment_stats
        ]

        # Invoice type breakdown
        type_stats = (
            db.query(
                Invoice.invoice_type,
                func.count(Invoice.id).label("count"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_revenue"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_count"
                ),
                func.sum(case((Invoice.status == "PENDING", 1), else_=0)).label(
                    "pending_count"
                ),
            )
            .filter(
                extract("year", Invoice.created_at) == year,
                extract("month", Invoice.created_at) == month,
            )
            .group_by(Invoice.invoice_type)
            .all()
        )

        invoice_type_breakdown = [
            InvoiceTypeBreakdown(
                invoice_type=stat.invoice_type,
                count=stat.count,
                total_revenue=float(stat.total_revenue or 0),
                paid_count=int(stat.paid_count or 0),
                pending_count=int(stat.pending_count or 0),
            )
            for stat in type_stats
        ]

        return MonthlyInvoiceAnalytics(
            month=f"{year}-{month:02d}",
            year=year,
            month_number=month,
            total_invoices=total_invoices,
            confirmed_invoices=confirmed_invoices,
            unconfirmed_invoices=unconfirmed_invoices,
            paid_count=paid_count,
            pending_count=pending_count,
            failed_count=failed_count,
            total_revenue=round(total_revenue, 2),
            pending_amount=round(pending_amount, 2),
            average_invoice_amount=round(average_invoice_amount, 2),
            conversion_rate=round(conversion_rate, 2),
            activity_breakdown=activity_breakdown,
            payment_method_breakdown=payment_method_breakdown,
            invoice_type_breakdown=invoice_type_breakdown,
        )

    @staticmethod
    def get_top_customers(db: Session, limit: int = 10) -> List[TopCustomerResponse]:
        """
        Get top customers by total spending.

        Args:
            db: Database session
            limit: Number of top customers to return
        """
        from sqlalchemy import case

        customer_stats = (
            db.query(
                Invoice.user_id,
                Invoice.buyer_name,
                Invoice.buyer_email,
                func.count(Invoice.id).label("total_invoices"),
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).label("total_spent"),
                func.sum(case((Invoice.status == "PAID", 1), else_=0)).label(
                    "paid_invoices"
                ),
                func.sum(case((Invoice.status == "PENDING", 1), else_=0)).label(
                    "pending_invoices"
                ),
            )
            .group_by(Invoice.user_id, Invoice.buyer_name, Invoice.buyer_email)
            .order_by(
                func.sum(
                    case((Invoice.status == "PAID", Invoice.amount), else_=0)
                ).desc()
            )
            .limit(limit)
            .all()
        )

        return [
            TopCustomerResponse(
                user_id=stat.user_id,
                buyer_name=stat.buyer_name,
                buyer_email=stat.buyer_email,
                total_invoices=stat.total_invoices,
                total_spent=round(float(stat.total_spent or 0), 2),
                paid_invoices=int(stat.paid_invoices or 0),
                pending_invoices=int(stat.pending_invoices or 0),
            )
            for stat in customer_stats
        ]
