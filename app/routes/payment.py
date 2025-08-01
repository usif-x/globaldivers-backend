from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.payment import PaymentService

payment_routes = APIRouter(prefix="/payment", tags=["Payment Endpoints"])


@payment_routes.get("/methods")
async def get_payment_methods(db: Session = Depends(get_db)):
    return PaymentService(db).get_payment_methods()
