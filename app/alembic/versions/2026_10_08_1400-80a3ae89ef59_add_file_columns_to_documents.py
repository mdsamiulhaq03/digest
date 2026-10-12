"""add file columns to documents

Revision ID: 80a3ae89ef59
Revises: 61e3404f31a8
Create Date: 2026-10-08 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "80a3ae89ef59"
down_revision: str | Sequence[str] | None = "61e3404f31a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A document comes from exactly one source: pasted text, or an uploaded file
# with all of its metadata. Never both, never neither, never half a file.
SOURCE_CHECK = (
    "(text IS NOT NULL AND original_filename IS NULL AND storage_key IS NULL"
    " AND size_bytes IS NULL AND content_type IS NULL)"
    " OR "
    "(text IS NULL AND original_filename IS NOT NULL AND storage_key IS NOT NULL"
    " AND size_bytes IS NOT NULL AND content_type IS NOT NULL)"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("documents", "text", existing_type=sa.Text(), nullable=True)
    op.add_column(
        "documents", sa.Column("original_filename", sa.String(255), nullable=True)
    )
    op.add_column("documents", sa.Column("storage_key", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("documents", sa.Column("content_type", sa.String(100), nullable=True))
    # Every existing row has text and no file, so it already satisfies this.
    op.create_check_constraint("ck_documents_source", "documents", SOURCE_CHECK)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_documents_source", "documents", type_="check")
    # Uploaded documents have no text, so they can't survive text going back
    # to NOT NULL. Their files stay on the volume; only the rows go.
    op.execute("DELETE FROM documents WHERE text IS NULL")
    op.drop_column("documents", "content_type")
    op.drop_column("documents", "size_bytes")
    op.drop_column("documents", "storage_key")
    op.drop_column("documents", "original_filename")
    op.alter_column("documents", "text", existing_type=sa.Text(), nullable=False)
