from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.request_context import REQUEST_ID_HEADER
from app.main import app

client = TestClient(app)


@pytest.fixture
def crashing_client() -> Iterator[TestClient]:
    """The unhandled-crash path needs a route that actually blows up.

    Registered on the real app so the test exercises the real middleware and
    handler wiring rather than a stand-in, then removed so no other test sees
    it. `raise_server_exceptions=False` makes TestClient return the 500 the way
    a real client would instead of re-raising it here."""

    async def boom() -> None:
        raise RuntimeError("deliberate test crash")

    app.add_api_route("/_test_boom", boom, methods=["GET"])
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.router.routes = [
            route
            for route in app.router.routes
            if getattr(route, "path", None) != "/_test_boom"
        ]


def test_response_carries_a_generated_request_id() -> None:
    response = client.get("/health")
    assert response.headers[REQUEST_ID_HEADER]


def test_client_supplied_request_id_is_reused() -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "caller-abc-123"})
    assert response.headers[REQUEST_ID_HEADER] == "caller-abc-123"


def test_not_found_uses_the_error_contract() -> None:
    response = client.get(
        "/documents/does-not-exist", headers={REQUEST_ID_HEADER: "r1"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {"message": "Document does-not-exist not found", "request_id": "r1"}
    }
    assert response.headers[REQUEST_ID_HEADER] == "r1"


def test_validation_error_uses_the_error_contract() -> None:
    response = client.post(
        "/documents",
        json={"title": "", "text": "hi"},
        headers={REQUEST_ID_HEADER: "r2"},
    )

    assert response.status_code == 422
    body = response.json()

    # FastAPI's default shape is a bare top-level "detail" list. Ours must win,
    # otherwise a client has to parse two different error formats.
    assert "detail" not in body
    assert body["error"]["message"] == "Request validation failed"
    assert body["error"]["request_id"] == "r2"
    assert body["error"]["details"][0]["loc"] == ["body", "title"]


def test_unhandled_crash_returns_the_contract_and_leaks_nothing(
    crashing_client: TestClient,
) -> None:
    response = crashing_client.get(
        "/_test_boom", headers={REQUEST_ID_HEADER: "crash-xyz"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {"message": "Internal server error", "request_id": "crash-xyz"}
    }

    # The ID is what a user quotes when reporting the failure, so it has to be
    # on the header too - not only in a body they may never look at.
    assert response.headers[REQUEST_ID_HEADER] == "crash-xyz"

    # Everything about the actual exception stays in the logs.
    assert "deliberate test crash" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
