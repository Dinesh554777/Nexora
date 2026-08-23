"""add patients and analyses tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(length=64), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("sex", sa.String(length=16), nullable=False),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_patient_id"), "patients", ["patient_id"], unique=True)

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("image_filename", sa.String(length=512), nullable=True),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_patient_id"), "analyses", ["patient_id"], unique=False)
    op.create_index(op.f("ix_analyses_status"), "analyses", ["status"], unique=False)

    with op.batch_alter_table("predictions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("analysis_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            op.f("ix_predictions_analysis_id"), ["analysis_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_predictions_analysis_id_analyses",
            "analyses",
            ["analysis_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("predictions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_predictions_analysis_id_analyses", type_="foreignkey")
        batch_op.drop_index(op.f("ix_predictions_analysis_id"))
        batch_op.drop_column("analysis_id")

    op.drop_index(op.f("ix_analyses_status"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_patient_id"), table_name="analyses")
    op.drop_table("analyses")

    op.drop_index(op.f("ix_patients_patient_id"), table_name="patients")
    op.drop_table("patients")
