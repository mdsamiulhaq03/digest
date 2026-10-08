"""add owner to documents

Revision ID: 61e3404f31a8
Revises: a801b5e419ac
Create Date: 2026-10-08 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "61e3404f31a8"
down_revision: str | Sequence[str] | None = "a801b5e419ac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Documents created before users existed need an owner before the column can
# be NOT NULL. They go to one fixed system account: a known id so downgrade
# can find it again, inactive and with a password hash no argon2 verify will
# ever accept, so nobody can log in as it.
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000001"
SYSTEM_USER_EMAIL = "system@digest.internal"
UNUSABLE_PASSWORD_HASH = "!"


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Nullable first - existing rows have no owner yet.
    op.add_column("documents", sa.Column("owner_id", sa.UUID(), nullable=True))

    # 2. Create the system account only when there is something to adopt, so a
    #    fresh database never gets a stray user row.
    op.execute(
        sa.text(
            "INSERT INTO users (id, email, password_hash, role, is_active) "
            "SELECT CAST(:id AS uuid), :email, :password_hash, 'admin', false "
            "WHERE EXISTS (SELECT 1 FROM documents WHERE owner_id IS NULL)"
        ).bindparams(
            id=SYSTEM_USER_ID,
            email=SYSTEM_USER_EMAIL,
            password_hash=UNUSABLE_PASSWORD_HASH,
        )
    )
    op.execute(
        sa.text(
            "UPDATE documents SET owner_id = CAST(:id AS uuid) WHERE owner_id IS NULL"
        ).bindparams(id=SYSTEM_USER_ID)
    )

    # 3. Every row has an owner now, so the constraint can hold.
    op.alter_column("documents", "owner_id", nullable=False)
    op.create_foreign_key(
        op.f("fk_documents_owner_id_users"),
        "documents",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Every list is "this owner's documents, newest first" - one composite
    # index serves both the filter and the sort.
    op.create_index(
        op.f("ix_documents_owner_id_created_at"),
        "documents",
        ["owner_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_documents_owner_id_created_at"), table_name="documents")
    op.drop_constraint(
        op.f("fk_documents_owner_id_users"), "documents", type_="foreignkey"
    )
    op.drop_column("documents", "owner_id")
    # Ownership is gone, so the account that only existed to hold it goes too.
    op.execute(
        sa.text("DELETE FROM users WHERE id = CAST(:id AS uuid)").bindparams(
            id=SYSTEM_USER_ID
        )
    )
