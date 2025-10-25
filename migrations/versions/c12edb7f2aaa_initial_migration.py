"""initial migration

Revision ID: c12edb7f2aaa
Revises:
Create Date: 2025-10-25 13:47:49.527590

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c12edb7f2aaa"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Initial migration - marks the starting point.
    Production database already has all tables, so this does nothing.
    """
    pass


def downgrade() -> None:
    """
    No downgrade needed for initial migration.
    """
    pass
