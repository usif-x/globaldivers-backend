# app/models/invoice.py

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    buyer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    buyer_email: Mapped[str] = mapped_column(String(100), nullable=False)
    buyer_phone: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_description: Mapped[str] = mapped_column(Text, nullable=False)
    activity: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(50), default="easykash", nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)

    # --- CORRECTIONS HERE ---
    customer_reference: Mapped[str] = mapped_column(
        String(50), nullable=True, unique=True
    )
    easykash_reference: Mapped[str] = mapped_column(
        String(50), nullable=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="invoices", lazy="joined"
    )
