"""add patient management fields (name, contact_info, is_active)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("patients", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("contact_info", sa.String(length=256), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("patients", schema=None) as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("contact_info")
        batch_op.drop_column("name")
