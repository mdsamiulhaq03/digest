"""Importing every model here keeps Alembic autogenerate honest: env.py imports
this package, so a new model file is picked up by adding it to this list only."""

from app.models.csv_insight import CsvInsight
from app.models.document import Document
from app.models.insight import Insight
from app.models.job import Job
from app.models.user import User

__all__ = ["CsvInsight", "Document", "Insight", "Job", "User"]
