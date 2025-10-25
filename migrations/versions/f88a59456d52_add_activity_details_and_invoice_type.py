"""add_activity_details_and_invoice_type

Revision ID: f88a59456d52
Revises: c12edb7f2aaa
Create Date: 2025-10-25 13:49:14.142119

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f88a59456d52"
down_revision: Union[str, None] = "c12edb7f2aaa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add activity_details column to invoices table if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'invoices' AND column_name = 'activity_details'
            ) THEN
                ALTER TABLE invoices ADD COLUMN activity_details JSONB;
            END IF;
        END $$;
    """
    )

    # Add invoice_type column to invoices table if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'invoices' AND column_name = 'invoice_type'
            ) THEN
                ALTER TABLE invoices ADD COLUMN invoice_type VARCHAR(20) DEFAULT 'online' NOT NULL;
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    # Remove the columns if downgrading
    op.drop_column("invoices", "invoice_type")
    op.drop_column("invoices", "activity_details")
