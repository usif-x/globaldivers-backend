"""add activity availability

Revision ID: add_activity_availability
Revises:
Create Date: 2026-01-01 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_activity_availability"
down_revision: Union[str, None] = None  # UPDATE THIS to your latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create activity_availability table
    op.create_table(
        "activity_availability",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("activity_type", sa.String(length=20), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "activity_type", "activity_id", "date", name="uq_activity_date"
        ),
    )

    # Create index for faster lookups
    op.create_index(
        "ix_activity_availability_lookup",
        "activity_availability",
        ["activity_type", "activity_id", "date"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_availability_lookup", table_name="activity_availability")
    op.drop_table("activity_availability")
