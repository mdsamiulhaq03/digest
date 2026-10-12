"""CORS: exact origins from configuration, never a wildcard, and off by default."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.cors import add_cors
from app.main import app

ALLOWED = "https://allowed.example.com"
OTHER = "https://evil.example.com"


def _settings(monkeypatch: pytest.MonkeyPatch, cors_origins: str | None) -> Settings:
    if cors_origins is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", cors_origins)
    return Settings(_env_file=None)


def _client_with(origins: list[str]) -> TestClient:
    test_app = FastAPI()
    add_cors(test_app, origins)

    @test_app.get("/thing")
    def thing() -> dict[str, str]:
        return {"ok": "yes"}

    return TestClient(test_app)


def test_no_origins_allowed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _settings(monkeypatch, None).cors_origins == []


def test_origins_are_read_comma_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(monkeypatch, f" {ALLOWED} , http://localhost:3000 ")
    assert settings.cors_origins == [ALLOWED, "http://localhost:3000"]


@pytest.mark.parametrize(
    "bad",
    [
        "*",
        "https://*.example.com",
        f"{ALLOWED}/",  # trailing slash: browsers never send one, so never matches
        f"{ALLOWED}/app",
        "allowed.example.com",  # no scheme
        "ftp://allowed.example.com",
    ],
)
def test_anything_but_an_exact_origin_stops_startup(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    with pytest.raises(ValidationError, match="CORS"):
        _settings(monkeypatch, f"{ALLOWED},{bad}")


def test_an_allowed_origin_can_read_responses() -> None:
    response = _client_with([ALLOWED]).get("/thing", headers={"Origin": ALLOWED})
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()
    # Bearer tokens, not cookies: credentials are never allowed cross-origin.
    assert "access-control-allow-credentials" not in response.headers


def test_an_unlisted_origin_gets_no_cors_headers() -> None:
    response = _client_with([ALLOWED]).get("/thing", headers={"Origin": OTHER})
    assert "access-control-allow-origin" not in response.headers


def test_preflight_from_an_unlisted_origin_is_refused() -> None:
    preflight = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization",
    }
    client = _client_with([ALLOWED])
    allowed = client.options("/thing", headers={"Origin": ALLOWED, **preflight})
    refused = client.options("/thing", headers={"Origin": OTHER, **preflight})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == ALLOWED
    assert refused.status_code == 400
    assert "access-control-allow-origin" not in refused.headers


def test_with_no_origins_the_middleware_is_not_installed() -> None:
    test_app = FastAPI()
    add_cors(test_app, [])
    assert test_app.user_middleware == []


def test_the_app_as_configured_by_default_sends_no_cors_headers() -> None:
    response = TestClient(app).get("/health/live", headers={"Origin": OTHER})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
