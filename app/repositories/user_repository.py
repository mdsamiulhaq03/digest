import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError
from app.models.user import User

# Postgres' default name for the UniqueConstraint("email") in the users migration.
EMAIL_UNIQUE_CONSTRAINT = "users_email_key"


class UserRepository:
    """Stages changes but never commits: the service decides where a unit of
    work ends, so several writes can succeed or fail together."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        try:
            # Flush sends the INSERT now, so a duplicate email surfaces here
            # as a domain error rather than later at the service's commit.
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            # Two sign-ups for one email can both pass the service's lookup;
            # the unique constraint is what actually decides the race.
            if _violated_constraint(exc) == EMAIL_UNIQUE_CONSTRAINT:
                raise EmailAlreadyRegisteredError() from exc
            raise
        self.db.refresh(user)
        return user

    def commit(self) -> None:
        self.db.commit()

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalars(select(User).where(User.email == email)).first()

    def list_all(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at.desc())))


def _violated_constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
