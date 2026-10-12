import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.document import Document


class CsvInsight(Base):
    __tablename__ = "csv_insights"
    __table_args__ = (
        CheckConstraint("row_count >= 0", name="ck_csv_insights_row_count"),
        CheckConstraint("column_count >= 0", name="ck_csv_insights_column_count"),
    )

    # Keyed on the document, so re-running a job upserts instead of creating a
    # second set of insights.
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
            name="fk_csv_insights_document_id_documents",
        ),
        primary_key=True,
    )
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # One entry per CSV column: name, null_count, inferred_type, min, max, mean.
    columns: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="csv_insight")
