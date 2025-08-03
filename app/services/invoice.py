import math
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.invoice import Invoice
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
from app.services.payment import PaymentService


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_service = PaymentService()

    @db_exception_handler
    async def create_invoice(self, invoice_data: InvoiceCreate) -> InvoiceResponse:
        """Create a new invoice"""

        # Generate payment URL if not provided
        pay_url = invoice_data.pay_url
        if not pay_url:
            pay_url = await self.payment_service.generate_payment_url(
                amount=invoice_data.amount,
                payment_method=invoice_data.pay_method,
                user_id=invoice_data.user_id,
                invoice_for=invoice_data.invoice_for,
            )

        # Create new invoice instance
        db_invoice = Invoice(
            user_id=invoice_data.user_id,
            amount=invoice_data.amount,
            status=invoice_data.status.value,
            pay_method=invoice_data.pay_method.value,
            invoice_for=invoice_data.invoice_for.value,
            items=invoice_data.items,
            pay_url=pay_url,
        )

        self.db.add(db_invoice)
        self.db.commit()
        self.db.refresh(db_invoice)

        # Convert to response model and include user data if needed
        invoice_response = InvoiceResponse.model_validate(db_invoice)
        if db_invoice.user:
            invoice_response.user = UserResponse.model_validate(db_invoice.user)

        return invoice_response

    @db_exception_handler
    async def get_invoice_by_id(self, invoice_id: int) -> InvoiceResponse:
        """Get invoice by ID"""

        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Convert to response model and include user data if needed
        invoice_response = InvoiceResponse.model_validate(invoice)
        if invoice.user:
            invoice_response.user = UserResponse.model_validate(invoice.user)

        return invoice_response

    @db_exception_handler
    async def get_invoices_by_user(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 10,
        status: Optional[InvoiceStatus] = None,
    ) -> InvoiceList:
        """Get invoices for a specific user with pagination"""

        # Base query
        stmt = select(Invoice).where(Invoice.user_id == user_id)

        # Add status filter if provided
        if status:
            stmt = stmt.where(Invoice.status == status.value)

        # Order by created_at descending
        stmt = stmt.order_by(Invoice.created_at.desc())

        # Count total invoices
        count_stmt = select(func.count(Invoice.id)).where(Invoice.user_id == user_id)
        if status:
            count_stmt = count_stmt.where(Invoice.status == status.value)

        total = self.db.execute(count_stmt).scalar()

        # Apply pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = self.db.execute(stmt)
        invoices = result.scalars().all()

        # Calculate total pages
        pages = math.ceil(total / per_page) if total > 0 else 1

        # Convert invoices to response models with user data
        invoice_responses = []
        for invoice in invoices:
            invoice_response = InvoiceResponse.model_validate(invoice)
            if invoice.user:
                invoice_response.user = UserResponse.model_validate(invoice.user)
            invoice_responses.append(invoice_response)

        return InvoiceList(
            invoices=invoice_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    @db_exception_handler
    async def get_all_invoices(
        self, page: int = 1, per_page: int = 10, status: Optional[InvoiceStatus] = None
    ) -> InvoiceList:
        """Get all invoices with pagination (admin function)"""

        # Base query
        stmt = select(Invoice)

        # Add status filter if provided
        if status:
            stmt = stmt.where(Invoice.status == status.value)

        # Order by created_at descending
        stmt = stmt.order_by(Invoice.created_at.desc())

        # Count total invoices
        count_stmt = select(func.count(Invoice.id))
        if status:
            count_stmt = count_stmt.where(Invoice.status == status.value)

        total = self.db.execute(count_stmt).scalar()

        # Apply pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = self.db.execute(stmt)
        invoices = result.scalars().all()

        # Calculate total pages
        pages = math.ceil(total / per_page) if total > 0 else 1

        # Convert invoices to response models with user data
        invoice_responses = []
        for invoice in invoices:
            invoice_response = InvoiceResponse.model_validate(invoice)
            if invoice.user:
                invoice_response.user = UserResponse.model_validate(invoice.user)
            invoice_responses.append(invoice_response)

        return InvoiceList(
            invoices=invoice_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    @db_exception_handler
    async def update_invoice(
        self, invoice_id: int, invoice_data: InvoiceUpdate
    ) -> InvoiceResponse:
        """Update an existing invoice"""

        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Update fields if provided
        update_data = invoice_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in ["status", "pay_method", "invoice_for"] and hasattr(
                value, "value"
            ):
                setattr(invoice, field, value.value)
            else:
                setattr(invoice, field, value)

        self.db.commit()
        self.db.refresh(invoice)

        # Convert to response model and include user data if needed
        invoice_response = InvoiceResponse.model_validate(invoice)
        if invoice.user:
            invoice_response.user = UserResponse.model_validate(invoice.user)

        return invoice_response

    @db_exception_handler
    async def update_invoice_status(
        self, invoice_id: int, status_data: InvoiceStatusUpdate
    ) -> InvoiceResponse:
        """Update invoice status specifically"""

        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Update status
        invoice.status = status_data.status.value

        # Update payment URL if provided
        if status_data.pay_url:
            invoice.pay_url = status_data.pay_url

        self.db.commit()
        self.db.refresh(invoice)

        # Convert to response model and include user data if needed
        invoice_response = InvoiceResponse.model_validate(invoice)
        if invoice.user:
            invoice_response.user = UserResponse.model_validate(invoice.user)

        return invoice_response

    @db_exception_handler
    async def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice (soft delete by marking as cancelled)"""

        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status == InvoiceStatus.PAID.value:
            raise HTTPException(status_code=400, detail="Cannot delete a paid invoice")

        # Mark as cancelled instead of hard delete
        invoice.status = InvoiceStatus.CANCELLED.value

        self.db.commit()

        return True

    @db_exception_handler
    async def get_invoice_summary(
        self, user_id: Optional[int] = None
    ) -> InvoiceSummary:
        """Get invoice summary/analytics"""

        # Base query
        base_query = select(Invoice)

        # Filter by user if provided
        if user_id:
            base_query = base_query.where(Invoice.user_id == user_id)

        # Get all invoices for calculations
        result = self.db.execute(base_query)
        invoices = result.scalars().all()

        # Calculate summary statistics
        total_invoices = len(invoices)
        total_amount = sum(invoice.amount for invoice in invoices)

        pending_invoices = len(
            [i for i in invoices if i.status == InvoiceStatus.PENDING.value]
        )
        pending_amount = sum(
            i.amount for i in invoices if i.status == InvoiceStatus.PENDING.value
        )

        paid_invoices = len(
            [i for i in invoices if i.status == InvoiceStatus.PAID.value]
        )
        paid_amount = sum(
            i.amount for i in invoices if i.status == InvoiceStatus.PAID.value
        )

        failed_invoices = len(
            [i for i in invoices if i.status == InvoiceStatus.FAILED.value]
        )
        failed_amount = sum(
            i.amount for i in invoices if i.status == InvoiceStatus.FAILED.value
        )

        return InvoiceSummary(
            total_invoices=total_invoices,
            total_amount=total_amount,
            pending_invoices=pending_invoices,
            pending_amount=pending_amount,
            paid_invoices=paid_invoices,
            paid_amount=paid_amount,
            failed_invoices=failed_invoices,
            failed_amount=failed_amount,
        )

    @db_exception_handler
    async def mark_invoice_as_paid(self, invoice_id: int) -> InvoiceResponse:
        """Mark an invoice as paid (typically called by payment webhook)"""

        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status == InvoiceStatus.PAID.value:
            raise HTTPException(status_code=400, detail="Invoice is already paid")

        invoice.status = InvoiceStatus.PAID.value

        self.db.commit()
        self.db.refresh(invoice)

        # Trigger any post-payment actions here if needed
        await self._handle_payment_success(invoice)

        # Convert to response model and include user data if needed
        invoice_response = InvoiceResponse.model_validate(invoice)
        if invoice.user:
            invoice_response.user = UserResponse.model_validate(invoice.user)

        return invoice_response

    @db_exception_handler
    async def mark_invoice_as_failed(self, invoice_id: int) -> InvoiceResponse:
        """Mark an invoice as failed (typically called by payment webhook)"""

        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice.status = InvoiceStatus.FAILED.value

        self.db.commit()
        self.db.refresh(invoice)

        # Convert to response model and include user data if needed
        invoice_response = InvoiceResponse.model_validate(invoice)
        if invoice.user:
            invoice_response.user = UserResponse.model_validate(invoice.user)

        return invoice_response

    async def _handle_payment_success(self, invoice: Invoice):
        """Handle post-payment actions (override in subclass if needed)"""
        # This method can be overridden to handle specific business logic
        # after successful payment (e.g., send confirmation email, activate services, etc.)
        pass

    @db_exception_handler
    async def get_invoices_by_status(
        self, status: InvoiceStatus
    ) -> List[InvoiceResponse]:
        """Get all invoices with a specific status"""

        stmt = select(Invoice).where(Invoice.status == status.value)
        result = self.db.execute(stmt)
        invoices = result.scalars().all()

        # Convert invoices to response models with user data
        invoice_responses = []
        for invoice in invoices:
            invoice_response = InvoiceResponse.model_validate(invoice)
            if invoice.user:
                invoice_response.user = UserResponse.model_validate(invoice.user)
            invoice_responses.append(invoice_response)

        return invoice_responses

    @db_exception_handler
    async def expire_pending_invoices(self, days_old: int = 7) -> int:
        """Expire invoices that have been pending for too long"""

        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = select(Invoice).where(
            Invoice.status == InvoiceStatus.PENDING.value,
            Invoice.created_at < cutoff_date,
        )

        result = self.db.execute(stmt)
        expired_invoices = result.scalars().all()

        count = 0
        for invoice in expired_invoices:
            invoice.status = InvoiceStatus.EXPIRED.value
            count += 1

        if count > 0:
            self.db.commit()

        return count
