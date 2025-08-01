from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

invoice_routes = APIRouter(prefix="/invoices", tags=["invoices Endpoints"])
