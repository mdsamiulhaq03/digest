import uuid
from dataclasses import asdict

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.csv_insight import CsvInsight
from app.models.insight import Insight
from app.utils.csv_insights import CsvInsights
from app.utils.insights import TextInsights


class InsightRepository:
    """Writes are upserts keyed on the document, so running a job twice
    replaces its insights instead of failing or duplicating them."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_text(self, document_id: uuid.UUID, insights: TextInsights) -> None:
        self._upsert(Insight, document_id, asdict(insights))

    def save_csv(self, document_id: uuid.UUID, insights: CsvInsights) -> None:
        self._upsert(CsvInsight, document_id, asdict(insights))

    def _upsert(
        self, model: type[Insight | CsvInsight], document_id: uuid.UUID, values: dict
    ) -> None:
        stmt = insert(model).values(document_id=document_id, **values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[model.document_id],
            set_={**values, "computed_at": func.now()},
        )
        self.db.execute(stmt)
