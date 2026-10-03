"""Importing every model here keeps Alembic autogenerate honest: env.py imports
this package, so a new model file is picked up by adding it to this list only."""

from app.models.document import Document
from app.models.insight import Insight

__all__ = ["Document", "Insight"]
