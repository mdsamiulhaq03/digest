from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ping(self) -> None:
        """Round-trip to Postgres. Raises SQLAlchemyError if it can't."""
        self.db.execute(text("SELECT 1"))
