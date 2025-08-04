from typing import Optional

from sqlalchemy import JSON, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.conn import Base


class WebsiteSettings(Base):
    __tablename__ = "website_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    website_title: Mapped[str] = mapped_column(String(100), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    default_currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="USD"
    )
    website_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'active'")
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    contact_whatsapp: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    social_links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
