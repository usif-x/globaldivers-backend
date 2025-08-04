from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import WebsiteSettings
from app.schemas.setting import WebsiteSettingsResponse, WebsiteSettingsUpdate


class WebsiteSettingsService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> WebsiteSettingsResponse:
        """
        Retrieves the website settings from the database.
        """
        settings = self.db.execute(select(WebsiteSettings)).scalar_one_or_none()
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Website settings not found. Please initialize them.",
            )
        return WebsiteSettingsResponse.model_validate(settings)

    def update_settings(
        self, settings_data: WebsiteSettingsUpdate
    ) -> WebsiteSettingsResponse:
        """
        Updates the website settings in the database.
        """
        try:
            db_settings = self.db.execute(select(WebsiteSettings)).scalar_one()

            # Get the update data as a dictionary, excluding unset fields
            update_data = settings_data.model_dump(exclude_unset=True)

            # Iterate over the update data and set attributes on the SQLAlchemy object
            for key, value in update_data.items():
                # Pydantic v2 url/email types need to be converted to strings for DB
                if hasattr(value, "build"):  # Heuristic for Pydantic special types
                    setattr(db_settings, key, str(value))
                elif isinstance(value, dict):
                    # Ensure nested social links are also strings
                    setattr(db_settings, key, {k: str(v) for k, v in value.items()})
                else:
                    setattr(db_settings, key, value)

            self.db.commit()
            self.db.refresh(db_settings)

            return self.get_settings()

        except Exception as e:
            self.db.rollback()
            # THIS IS THE FIX for the TypeError. We now return a simple string.
            # Your `db_exception_handler` is the root cause of the JSON error.
            # Using str(e) is a safe and informative fallback.
            print(
                f"An error occurred while updating settings: {e}"
            )  # Log the real error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )
