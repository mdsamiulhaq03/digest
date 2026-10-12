"""create csv_insights table

Revision ID: 2699d8dde48c
Revises: 2ee4635772f1
Create Date: 2026-10-08 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2699d8dde48c"
down_revision: str | Sequence[str] | None = "2ee4635772f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "csv_insights",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        # One entry per CSV column. Variable length and never queried per
        # column, so it lives as JSONB rather than in a child table.
        sa.Column("columns", postgresql.JSONB(), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("row_count >= 0", name="ck_csv_insights_row_count"),
        sa.CheckConstraint("column_count >= 0", name="ck_csv_insights_column_count"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_csv_insights_document_id_documents",
            ondelete="CASCADE",
        ),
        # Keyed on the document, so re-running a job upserts instead of
        # creating a second set of insights.
        sa.PrimaryKeyConstraint("document_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("csv_insights")
