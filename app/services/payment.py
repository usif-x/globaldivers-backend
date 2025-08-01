from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.utils.fawaterk import Fawaterk

fawaterk = Fawaterk()


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def get_payment_methods(self):
        try:
            return fawaterk.get_payment_methods()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
