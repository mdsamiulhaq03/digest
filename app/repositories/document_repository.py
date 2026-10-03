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

    def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        stmt = (
            select(Document)
            .options(selectinload(Document.insight))
            .where(Document.id == document_id)
        )
        return self.db.scalars(stmt).first()

    def list_all(self) -> list[Document]:
        stmt = (
            select(Document)
            .options(selectinload(Document.insight))
            .order_by(Document.created_at.desc())
        )
        return list(self.db.scalars(stmt))
