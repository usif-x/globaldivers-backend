from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.invoice import Invoice
from app.services.payment import PaymentService


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
