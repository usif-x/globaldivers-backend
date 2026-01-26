"""merge multiple heads

Revision ID: 7ed49fe7590f
Revises: add_activity_availability, c153c1facfeb
Create Date: 2026-01-26 15:49:44.659289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ed49fe7590f'
down_revision: Union[str, Sequence[str], None] = ('add_activity_availability', 'c153c1facfeb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
