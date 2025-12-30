"""Add is_confirmed and notes columns to invoices

Revision ID: c153c1facfeb
Revises: 31033176eb36
Create Date: 2025-12-30 14:08:01.550439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c153c1facfeb'
down_revision: Union[str, Sequence[str], None] = '31033176eb36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_confirmed column with default False
    op.add_column('invoices', sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='true'))
    # Add notes column for admin notes
    op.add_column('invoices', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the columns in reverse order
    op.drop_column('invoices', 'notes')
    op.drop_column('invoices', 'is_confirmed')
