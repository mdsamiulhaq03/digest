import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.csv_insight import CsvInsight
    from app.models.insight import Insight


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        # Every list is "this owner's documents, newest first".
        Index("ix_documents_owner_id_created_at", "owner_id", "created_at"),
        # Pasted text, or an uploaded file with all of its metadata - exactly one.
        CheckConstraint(
            "(text IS NOT NULL AND original_filename IS NULL AND storage_key IS NULL"
            " AND size_bytes IS NULL AND content_type IS NULL)"
            " OR "
            "(text IS NULL AND original_filename IS NOT NULL"
            " AND storage_key IS NOT NULL AND size_bytes IS NOT NULL"
            " AND content_type IS NOT NULL)",
            name="ck_documents_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_documents_owner_id_users"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # For display only - never used to build a path on disk.
    original_filename: Mapped[str | None] = mapped_column(String(255))
    # Relative to UPLOAD_DIR, so the volume can move without rewriting rows.
    storage_key: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    content_type: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # An uploaded document has neither until its job succeeds; after that it
    # has exactly one - text insights for .txt, CSV insights for .csv.
    insight: Mapped["Insight | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    csv_insight: Mapped["CsvInsight | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
