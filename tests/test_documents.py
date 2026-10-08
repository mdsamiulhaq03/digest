import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PASSWORD = "correct-horse-battery"


def _login_as(email: str) -> dict[str, str]:
    """Register a real user and return headers carrying their token."""
    client.post("/auth/register", json={"email": email, "password": PASSWORD})
    token = client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/documents"),
        ("GET", "/documents"),
        ("GET", f"/documents/{uuid.uuid4()}"),
    ],
    ids=["create", "list", "get"],
)
def test_document_routes_require_a_token(method: str, path: str) -> None:
    response = client.request(method, path, json={"title": "t", "text": "x"})
    assert response.status_code == 401


@pytest.mark.integration
def test_create_and_get_document() -> None:
    headers = _login_as("sam@example.com")
    response = client.post(
        "/documents",
        json={"title": "Test Doc", "text": "Hello world. Hello again!"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test Doc"
    assert body["insights"]["word_count"] == 4
    doc_id = body["id"]

    get_response = client.get(f"/documents/{doc_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == doc_id


def test_get_malformed_document_id_returns_404(as_some_user: None) -> None:
    response = client.get("/documents/does-not-exist")
    assert response.status_code == 404


@pytest.mark.integration
def test_get_missing_document_returns_404() -> None:
    headers = _login_as("sam@example.com")
    response = client.get(f"/documents/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


def test_create_document_invalid_payload_returns_422(as_some_user: None) -> None:
    response = client.post("/documents", json={"title": "", "text": "hi"})
    assert response.status_code == 422


@pytest.mark.integration
def test_list_documents_returns_newest_first() -> None:
    headers = _login_as("sam@example.com")
    client.post(
        "/documents",
        json={"title": "Older", "text": "First document."},
        headers=headers,
    )
    client.post(
        "/documents",
        json={"title": "Newer", "text": "Second document."},
        headers=headers,
    )

    response = client.get("/documents", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 2
    assert [d["title"] for d in body["documents"]] == ["Newer", "Older"]


@pytest.mark.integration
def test_another_users_document_is_a_404_and_never_listed() -> None:
    alice = _login_as("alice@example.com")
    bob = _login_as("bob@example.com")
    doc_id = client.post(
        "/documents", json={"title": "Alice's", "text": "Private."}, headers=alice
    ).json()["id"]

    # Same response as a document that doesn't exist at all.
    response = client.get(f"/documents/{doc_id}", headers=bob)
    assert response.status_code == 404
    assert client.get("/documents", headers=bob).json()["total"] == 0
    # And the owner still sees it.
    assert client.get(f"/documents/{doc_id}", headers=alice).status_code == 200
