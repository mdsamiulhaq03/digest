import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    # There is deliberately no unscoped read. Ownership is part of the query
    # itself, so no caller can fetch a document and forget to check whose it is.

    def get_for_owner(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Document | None:
        stmt = (
            select(Document)
            .options(selectinload(Document.insight))
            .where(Document.id == document_id, Document.owner_id == owner_id)
        )
        return self.db.scalars(stmt).first()

    def list_for_owner(self, owner_id: uuid.UUID) -> list[Document]:
        stmt = (
            select(Document)
            .options(selectinload(Document.insight))
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
        )
        return list(self.db.scalars(stmt))
