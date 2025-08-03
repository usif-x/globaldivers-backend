import asyncio
import random
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.schemas.invoice import InvoiceFor, PaymentMethod


class PaymentService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.base_url = "https://fake-payment-gateway.com"

    @db_exception_handler
    async def generate_payment_url(
        self,
        amount: float,
        payment_method: PaymentMethod,
        user_id: int,
        invoice_for: InvoiceFor,
        invoice_id: Optional[int] = None,
    ) -> str:
        """Generate a fake payment URL for testing"""

        # Simulate some processing time
        await asyncio.sleep(0.1)

        # Generate a fake transaction ID
        transaction_id = str(uuid.uuid4())[:8].upper()

        # Create different URL patterns based on payment method
        if payment_method == PaymentMethod.CREDIT_CARD:
            return f"{self.base_url}/card-payment/{transaction_id}?amount={amount}&user={user_id}"

        elif payment_method == PaymentMethod.FAWRY:
            return f"{self.base_url}/fawry-payment/{transaction_id}?amount={amount}&user={user_id}"

        elif payment_method == PaymentMethod.BANK_TRANSFER:
            return f"{self.base_url}/bank-transfer/{transaction_id}?amount={amount}&user={user_id}"

        elif payment_method == PaymentMethod.CASH:
            return f"{self.base_url}/cash-payment/{transaction_id}?amount={amount}&user={user_id}"

        else:
            return f"{self.base_url}/generic-payment/{transaction_id}?amount={amount}&user={user_id}"

    @db_exception_handler
    async def validate_payment(self, payment_url: str) -> dict:
        """Validate a payment URL and return payment details"""

        await asyncio.sleep(0.05)

        if not payment_url or not payment_url.startswith(self.base_url):
            raise HTTPException(status_code=400, detail="Invalid payment URL")

        # Extract transaction ID from URL
        try:
            transaction_id = payment_url.split("/")[-1].split("?")[0]
        except:
            raise HTTPException(status_code=400, detail="Invalid payment URL format")

        return {
            "transaction_id": transaction_id,
            "status": "valid",
            "gateway": "fake_payment_service",
            "created_at": "2024-01-01T00:00:00Z",
        }

    @db_exception_handler
    async def simulate_payment_process(self, payment_url: str) -> dict:
        """Simulate the payment processing (for testing purposes)"""

        # Simulate processing time
        await asyncio.sleep(random.uniform(1, 3))

        # Random success/failure for testing
        success_rate = 0.8  # 80% success rate
        is_successful = random.random() < success_rate

        transaction_id = payment_url.split("/")[-1].split("?")[0]

        if is_successful:
            return {
                "transaction_id": transaction_id,
                "status": "completed",
                "payment_status": "paid",
                "message": "Payment processed successfully",
                "gateway_response": {
                    "reference_number": f"REF{random.randint(100000, 999999)}",
                    "authorization_code": f"AUTH{random.randint(10000, 99999)}",
                    "processed_at": "2024-01-01T00:00:00Z",
                },
            }
        else:
            # Random failure reasons
            failure_reasons = [
                "Insufficient funds",
                "Card expired",
                "Transaction declined",
                "Network timeout",
                "Invalid card details",
            ]

            return {
                "transaction_id": transaction_id,
                "status": "failed",
                "payment_status": "failed",
                "message": random.choice(failure_reasons),
                "error_code": f"ERR_{random.randint(1000, 9999)}",
            }

    @db_exception_handler
    async def get_payment_status(self, transaction_id: str) -> dict:
        """Get payment status by transaction ID"""

        await asyncio.sleep(0.1)

        if not transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID is required")

        # Simulate different payment statuses
        statuses = ["pending", "processing", "completed", "failed", "cancelled"]
        status = random.choice(statuses)

        base_response = {
            "transaction_id": transaction_id,
            "status": status,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        if status == "completed":
            base_response.update(
                {
                    "payment_status": "paid",
                    "reference_number": f"REF{random.randint(100000, 999999)}",
                    "amount_paid": random.uniform(10, 1000),
                    "currency": "EGP",
                }
            )
        elif status == "failed":
            base_response.update(
                {
                    "payment_status": "failed",
                    "error_message": "Payment processing failed",
                    "error_code": f"ERR_{random.randint(1000, 9999)}",
                }
            )
        else:
            base_response.update(
                {
                    "payment_status": status,
                    "estimated_completion": "2024-01-01T01:00:00Z",
                }
            )

        return base_response

    @db_exception_handler
    async def cancel_payment(self, transaction_id: str) -> dict:
        """Cancel a pending payment"""

        await asyncio.sleep(0.2)

        if not transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID is required")

        # Simulate cancellation success/failure
        can_cancel = random.random() < 0.9  # 90% success rate for cancellation

        if can_cancel:
            return {
                "transaction_id": transaction_id,
                "status": "cancelled",
                "message": "Payment cancelled successfully",
                "cancelled_at": "2024-01-01T00:00:00Z",
            }
        else:
            raise HTTPException(
                status_code=400, detail="Cannot cancel payment - already processed"
            )

    @db_exception_handler
    async def refund_payment(
        self, transaction_id: str, amount: Optional[float] = None
    ) -> dict:
        """Process a refund for a completed payment"""

        await asyncio.sleep(0.5)

        if not transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID is required")

        # Simulate refund processing
        refund_successful = random.random() < 0.85  # 85% success rate

        if refund_successful:
            refund_id = str(uuid.uuid4())[:8].upper()
            refund_amount = amount or random.uniform(10, 1000)

            return {
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "status": "refunded",
                "refund_amount": refund_amount,
                "currency": "EGP",
                "message": "Refund processed successfully",
                "processed_at": "2024-01-01T00:00:00Z",
                "estimated_arrival": "3-5 business days",
            }
        else:
            raise HTTPException(
                status_code=400, detail="Refund failed - please contact support"
            )

    @db_exception_handler
    async def get_supported_payment_methods(self) -> list:
        """Get list of supported payment methods"""

        return [
            {
                "method": "credit_card",
                "name": "Credit Card",
                "description": "Visa, MasterCard, American Express",
                "fees": "2.9% + 0.30 EGP",
                "processing_time": "Instant",
            },
            {
                "method": "fawry",
                "name": "Fawry",
                "description": "Pay through Fawry network",
                "fees": "5.00 EGP",
                "processing_time": "Up to 2 hours",
            },
            {
                "method": "bank_transfer",
                "name": "Bank Transfer",
                "description": "Direct bank transfer",
                "fees": "Free",
                "processing_time": "1-3 business days",
            },
            {
                "method": "cash",
                "name": "Cash Payment",
                "description": "Pay in cash at collection point",
                "fees": "Free",
                "processing_time": "Instant upon collection",
            },
        ]

    @db_exception_handler
    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "EGP",
        payment_method: Optional[PaymentMethod] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a payment intent (similar to Stripe's payment intent)"""

        await asyncio.sleep(0.1)

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        intent_id = f"pi_{str(uuid.uuid4()).replace('-', '')[:24]}"
        client_secret = f"{intent_id}_secret_{str(uuid.uuid4())[:8]}"

        return {
            "id": intent_id,
            "client_secret": client_secret,
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
            "payment_method": payment_method.value if payment_method else None,
            "metadata": metadata or {},
            "created": "2024-01-01T00:00:00Z",
            "description": f"Payment for {amount} {currency}",
            "next_action": None,
            "confirmation_method": "automatic",
        }

    @db_exception_handler
    async def webhook_verify(self, payload: str, signature: str) -> bool:
        """Verify webhook signature (fake implementation)"""

        # In a real implementation, you'd verify the webhook signature
        # For fake service, we'll just simulate verification
        await asyncio.sleep(0.05)

        return len(payload) > 0 and len(signature) > 0

    def get_webhook_endpoints(self) -> dict:
        """Get webhook endpoint configuration"""

        return {
            "payment_success": "/invoices/webhook/payment-success/{invoice_id}",
            "payment_failed": "/invoices/webhook/payment-failed/{invoice_id}",
            "supported_events": [
                "payment.succeeded",
                "payment.failed",
                "payment.cancelled",
                "refund.created",
                "refund.succeeded",
            ],
        }
