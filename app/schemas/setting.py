from typing import Dict, Optional

from pydantic import BaseModel, EmailStr, HttpUrl


class WebsiteSettingsResponse(BaseModel):
    website_title: str
    logo_url: Optional[HttpUrl] = None
    default_currency: str = "USD"
    website_status: str = "active"
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    social_links: Optional[Dict[str, HttpUrl]] = None

    class Config:
        from_attributes = True


class WebsiteSettingsUpdate(BaseModel):
    website_title: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    default_currency: Optional[str] = None
    website_status: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    social_links: Optional[Dict[str, HttpUrl]] = None
