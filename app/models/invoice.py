from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.conn import Base

if TYPE_CHECKING:
    from .user import User


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    pay_url: Mapped[str] = mapped_column(String(255), nullable=False)
    pay_method: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_for: Mapped[str] = mapped_column(String(100), nullable=False)
    items: Mapped[List[dict]] = mapped_column(JSON, nullable=False)
    user: Mapped["User"] = relationship(back_populates="invoices", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<Invoice(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
        )
