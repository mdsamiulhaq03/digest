"""The migrations, run for real: up, down and up again, with rows in the way.

Each test gets a throwaway database of its own, so one that fails halfway
down the chain can't leave the shared test database at the wrong revision.
"""

import uuid
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import URL, Engine, create_engine, inspect, make_url, text
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  (registers every model with Base.metadata)
from app.core.config import get_settings
from app.core.db import Base
from tests.database import (
    TEST_DATABASE_SUFFIX,
    alembic_config,
    drop_database,
    recreate_database,
)

BEFORE_OWNERS = "a801b5e419ac"  # users exist, documents have no owner yet
BEFORE_UPLOADS = "61e3404f31a8"  # documents owned, but text-only
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000001"
APP_TABLES = {"users", "documents", "insights", "jobs", "csv_insights"}


@pytest.fixture
def scratch(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """An empty database, with settings - and so Alembic's env.py, which reads
    its URL from them - pointed at it for the length of the test."""
    url = _scratch_url()
    recreate_database(url)
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    get_settings.cache_clear()
    engine = create_engine(url, poolclass=NullPool)
    yield engine
    engine.dispose()
    monkeypatch.undo()
    get_settings.cache_clear()
    drop_database(url)


def _scratch_url() -> URL:
    url = make_url(get_settings().database_url)
    base = url.database.removesuffix(TEST_DATABASE_SUFFIX)
    return url.set(database=f"{base}_migrations{TEST_DATABASE_SUFFIX}")


def _upgrade(revision: str) -> None:
    command.upgrade(alembic_config(), revision)


def _downgrade(revision: str) -> None:
    command.downgrade(alembic_config(), revision)


def _revisions_oldest_first() -> list[str]:
    script = ScriptDirectory.from_config(alembic_config())
    return [revision.revision for revision in reversed(list(script.walk_revisions()))]


def _current_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def _app_tables(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names()) - {"alembic_version"}


def _schema_drift(engine: Engine) -> list:
    with engine.connect() as connection:
        return compare_metadata(MigrationContext.configure(connection), Base.metadata)


def _scalar(engine: Engine, sql: str, **params: object) -> object:
    with engine.connect() as connection:
        return connection.execute(text(sql), params).scalar_one()


def _insert_user(engine: Engine) -> uuid.UUID:
    user_id = uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO users (id, email, password_hash) VALUES (:id, :e, 'x')"),
            {"id": user_id, "e": f"{user_id}@example.com"},
        )
    return user_id


def _insert_pasted(engine: Engine, owner_id: uuid.UUID | None = None) -> uuid.UUID:
    document_id = uuid.uuid4()
    columns, values = "id, title, text", ":id, 'pasted', 'some text'"
    if owner_id is not None:
        columns, values = f"{columns}, owner_id", f"{values}, :owner"
    with engine.begin() as connection:
        connection.execute(
            text(f"INSERT INTO documents ({columns}) VALUES ({values})"),
            {"id": document_id, "owner": owner_id},
        )
        connection.execute(
            text(
                "INSERT INTO insights (document_id, char_count,"
                " char_count_no_whitespace, word_count, unique_word_count,"
                " sentence_count, paragraph_count, average_word_length, top_words,"
                " estimated_reading_time_seconds)"
                " VALUES (:id, 9, 8, 2, 2, 1, 1, 4.0, '[]', 0.6)"
            ),
            {"id": document_id},
        )
    return document_id


def _insert_upload(engine: Engine, owner_id: uuid.UUID) -> uuid.UUID:
    document_id = uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO documents (id, title, owner_id, original_filename,"
                " storage_key, size_bytes, content_type)"
                " VALUES (:id, 'upload', :owner, 'a.csv', :id, 4, 'text/csv')"
            ),
            {"id": document_id, "owner": owner_id},
        )
        connection.execute(
            text(
                "INSERT INTO jobs (id, document_id, state, attempts, finished_at)"
                " VALUES (:job, :id, 'succeeded', 1, now())"
            ),
            {"job": uuid.uuid4(), "id": document_id},
        )
        connection.execute(
            text(
                "INSERT INTO csv_insights (document_id, row_count, column_count,"
                " columns) VALUES (:id, 1, 1, '[]')"
            ),
            {"id": document_id},
        )
    return document_id


@pytest.mark.integration
def test_full_chain_goes_up_down_and_up_again_with_data(scratch: Engine) -> None:
    head = _revisions_oldest_first()[-1]
    _upgrade("head")
    owner = _insert_user(scratch)
    _insert_pasted(scratch, owner)
    _insert_upload(scratch, owner)

    _downgrade("base")
    assert _app_tables(scratch) == set()
    assert _current_revision(scratch) is None

    _upgrade("head")
    assert _app_tables(scratch) == APP_TABLES
    assert _current_revision(scratch) == head
    assert _schema_drift(scratch) == []


@pytest.mark.integration
def test_every_revision_can_be_undone_and_reapplied(scratch: Engine) -> None:
    """Walk up one step at a time, undoing and redoing each step. A downgrade
    that leaves something behind (an index, a constraint) fails the redo."""
    for revision in _revisions_oldest_first():
        _upgrade(revision)
        _downgrade("-1")
        _upgrade(revision)
        assert _current_revision(scratch) == revision


@pytest.mark.integration
def test_models_match_what_the_migrations_build(scratch: Engine) -> None:
    """A model changed without a migration shows up here as a difference."""
    _upgrade("head")
    assert _schema_drift(scratch) == []


@pytest.mark.integration
def test_documents_from_before_users_go_to_a_locked_system_account(
    scratch: Engine,
) -> None:
    _upgrade(BEFORE_OWNERS)
    document_id = _insert_pasted(scratch)

    _upgrade("head")
    owner = _scalar(
        scratch, "SELECT owner_id FROM documents WHERE id = :id", id=document_id
    )
    assert str(owner) == SYSTEM_USER_ID
    is_active = _scalar(
        scratch, "SELECT is_active FROM users WHERE id = :id", id=SYSTEM_USER_ID
    )
    assert is_active is False
    password_hash = _scalar(
        scratch, "SELECT password_hash FROM users WHERE id = :id", id=SYSTEM_USER_ID
    )
    assert password_hash == "!"

    _downgrade(BEFORE_OWNERS)
    assert _scalar(scratch, "SELECT count(*) FROM users") == 0
    assert _scalar(scratch, "SELECT count(*) FROM documents") == 1


@pytest.mark.integration
def test_a_fresh_database_gets_no_system_account(scratch: Engine) -> None:
    _upgrade("head")
    assert _scalar(scratch, "SELECT count(*) FROM users") == 0


@pytest.mark.integration
def test_downgrading_past_uploads_drops_uploads_and_keeps_pasted_text(
    scratch: Engine,
) -> None:
    _upgrade("head")
    owner = _insert_user(scratch)
    pasted = _insert_pasted(scratch, owner)
    _insert_upload(scratch, owner)

    _downgrade(BEFORE_UPLOADS)
    remaining = _scalar(scratch, "SELECT array_agg(id) FROM documents")
    assert remaining == [pasted]
    nullable = _scalar(
        scratch,
        "SELECT is_nullable FROM information_schema.columns"
        " WHERE table_name = 'documents' AND column_name = 'text'",
    )
    assert nullable == "NO"
