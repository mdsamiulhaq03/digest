"""create jobs table

Revision ID: 2ee4635772f1
Revises: 80a3ae89ef59
Create Date: 2026-10-08 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ee4635772f1"
down_revision: str | Sequence[str] | None = "80a3ae89ef59"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("state", sa.String(20), server_default="queued", nullable=False),
        sa.Column("attempts", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_jobs_state",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_jobs_attempts_non_negative"),
        # A job has a finish time exactly when it has finished.
        sa.CheckConstraint(
            "(state IN ('succeeded', 'failed')) = (finished_at IS NOT NULL)",
            name="ck_jobs_finished_at",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_jobs_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", name="uq_jobs_document_id"),
    )
    # The sweeper only ever looks for running jobs, a small set at any moment.
    op.create_index(
        "ix_jobs_running_started_at",
        "jobs",
        ["started_at"],
        unique=False,
        postgresql_where=sa.text("state = 'running'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_jobs_running_started_at",
        table_name="jobs",
        postgresql_where=sa.text("state = 'running'"),
    )
    op.drop_table("jobs")
