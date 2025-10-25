"""add_missing_invoice_columns

Revision ID: 775d60ff21d6
Revises: 32adeb600fda
Create Date: 2025-10-25 13:35:44.268020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '775d60ff21d6'
down_revision: Union[str, Sequence[str], None] = '32adeb600fda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
