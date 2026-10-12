"""The test suite's own Postgres database, built by the migrations.

Tests used to share the development database and truncate it, so every
`make test` wiped whatever had been created locally. They now get a database
of their own on the same server - the same name with `_test` appended -
created from nothing and migrated with Alembic at the start of each run. If a
migration is broken, the test run is what notices.

Redis gets the same treatment: tests use a logical database of their own, so
the development worker never takes a test's job off the shared queue.
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, create_engine, make_url, text

from app.core.config import get_settings

TEST_DATABASE_SUFFIX = "_test"
TEST_REDIS_DB = 15  # the last of Redis's 16 default databases; the app uses 0
ALEMBIC_SCRIPTS = Path(__file__).resolve().parents[1] / "app" / "alembic"


def use_test_database() -> None:
    """Point the app at the test Postgres and Redis databases. Must run before
    anything imports app.core.db, which builds its engine at import time."""
    settings = get_settings()
    url = _with_test_suffix(make_url(settings.database_url))
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    os.environ["REDIS_URL"] = (
        urlsplit(settings.redis_url)._replace(path=f"/{TEST_REDIS_DB}").geturl()
    )
    get_settings.cache_clear()


def create_test_database() -> None:
    """Drop and recreate the test database, then migrate it to head. Starting
    from empty on every run proves the whole migration chain still applies."""
    recreate_database(make_url(get_settings().database_url))
    command.upgrade(alembic_config(), "head")


def recreate_database(url: URL) -> None:
    _run_on_server(url, f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)')
    _run_on_server(url, f'CREATE DATABASE "{url.database}"')


def drop_database(url: URL) -> None:
    _run_on_server(url, f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)')


def _run_on_server(url: URL, statement: str) -> None:
    if not url.database.endswith(TEST_DATABASE_SUFFIX):
        # The guard that keeps a missed use_test_database() from dropping
        # the development database.
        raise RuntimeError(f"refusing to touch non-test database {url.database}")
    server = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with server.connect() as connection:
        connection.execute(text(statement))
    server.dispose()


def _with_test_suffix(url: URL) -> URL:
    if url.database.endswith(TEST_DATABASE_SUFFIX):
        return url
    return url.set(database=f"{url.database}{TEST_DATABASE_SUFFIX}")


def alembic_config() -> Config:
    # Built without alembic.ini on purpose: env.py would otherwise apply the
    # ini's logging config and replace the app's logging mid-run.
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_SCRIPTS))
    config.set_main_option("path_separator", "os")
    return config
