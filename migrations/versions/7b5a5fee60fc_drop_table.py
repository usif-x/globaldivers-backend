"""drop table

Revision ID: 7b5a5fee60fc
Revises: 6e67722c70e5
Create Date: 2025-10-25 15:21:56.645582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b5a5fee60fc'
down_revision: Union[str, Sequence[str], None] = '6e67722c70e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
