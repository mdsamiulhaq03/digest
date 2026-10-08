import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document


class DocumentRepository:
    """Stages changes but never commits: the service decides where a unit of
    work ends, so several writes can succeed or fail together."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        self.db.refresh(document)
        return document

    def commit(self) -> None:
        self.db.commit()

    # There is deliberately no unscoped read. Ownership is part of the query
    # itself, so no caller can fetch a document and forget to check whose it is.

    def get_for_owner(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Document | None:
        stmt = _with_insights(select(Document)).where(
            Document.id == document_id, Document.owner_id == owner_id
        )
        return self.db.scalars(stmt).first()

    def list_for_owner(self, owner_id: uuid.UUID) -> list[Document]:
        stmt = (
            _with_insights(select(Document))
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
        )
        return list(self.db.scalars(stmt))


def _with_insights(stmt: Select[tuple[Document]]) -> Select[tuple[Document]]:
    # Loaded up front so a list never issues one extra query per document.
    return stmt.options(
        selectinload(Document.insight), selectinload(Document.csv_insight)
    )
