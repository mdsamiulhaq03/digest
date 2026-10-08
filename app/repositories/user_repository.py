import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError
from app.models.user import User

# Postgres' default name for the UniqueConstraint("email") in the users migration.
EMAIL_UNIQUE_CONSTRAINT = "users_email_key"


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            # Two sign-ups for one email can both pass the service's lookup;
            # the unique constraint is what actually decides the race.
            if _violated_constraint(exc) == EMAIL_UNIQUE_CONSTRAINT:
                raise EmailAlreadyRegisteredError() from exc
            raise
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalars(select(User).where(User.email == email)).first()

    def list_all(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at.desc())))


def _violated_constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
