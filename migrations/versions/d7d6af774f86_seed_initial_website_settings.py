"""Seed initial website settings

Revision ID: d7d6af774f86
Revises: 207515d9d8e8
Create Date: 2025-08-04 14:49:55.679618

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7d6af774f86"
down_revision: Union[str, Sequence[str], None] = "207515d9d8e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the table object to insert into
    settings_table = sa.table(
        "website_settings",
        sa.column("website_title", sa.String),
        sa.column("logo_url", sa.String),
        sa.column("default_currency", sa.String),
        sa.column("website_status", sa.String),
        sa.column("contact_phone", sa.String),
        sa.column("contact_whatsapp", sa.String),
        sa.column("contact_email", sa.String),
        sa.column("social_links", sa.JSON),
    )

    # Insert the single, initial row of settings
    op.bulk_insert(
        settings_table,
        [
            {
                "website_title": "My Awesome Website",
                "logo_url": None,
                "default_currency": "USD",
                "website_status": "active",
                "contact_phone": None,
                "contact_whatsapp": None,
                "contact_email": "contact@example.com",
                "social_links": None,
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
