import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.factories import login_as

client = TestClient(app)


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
    sam = login_as("sam@example.com")
    response = client.post(
        "/documents",
        json={"title": "Test Doc", "text": "Hello world. Hello again!"},
        headers=sam.headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test Doc"
    assert body["insights"]["word_count"] == 4
    doc_id = body["id"]

    get_response = client.get(f"/documents/{doc_id}", headers=sam.headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == doc_id


def test_get_malformed_document_id_returns_404(as_some_user: None) -> None:
    response = client.get("/documents/does-not-exist")
    assert response.status_code == 404


@pytest.mark.integration
def test_get_missing_document_returns_404() -> None:
    sam = login_as("sam@example.com")
    response = client.get(f"/documents/{uuid.uuid4()}", headers=sam.headers)
    assert response.status_code == 404


def test_create_document_invalid_payload_returns_422(as_some_user: None) -> None:
    response = client.post("/documents", json={"title": "", "text": "hi"})
    assert response.status_code == 422


@pytest.mark.integration
def test_list_documents_returns_newest_first() -> None:
    sam = login_as("sam@example.com")
    for title, text in [("Older", "First document."), ("Newer", "Second document.")]:
        client.post(
            "/documents", json={"title": title, "text": text}, headers=sam.headers
        )

    response = client.get("/documents", headers=sam.headers)
    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 2
    assert [d["title"] for d in body["documents"]] == ["Newer", "Older"]


@pytest.mark.integration
def test_another_users_document_is_a_404_and_never_listed() -> None:
    alice = login_as("alice@example.com")
    bob = login_as("bob@example.com")
    doc_id = client.post(
        "/documents",
        json={"title": "Alice's", "text": "Private."},
        headers=alice.headers,
    ).json()["id"]

    # Same response as a document that doesn't exist at all.
    response = client.get(f"/documents/{doc_id}", headers=bob.headers)
    assert response.status_code == 404
    assert client.get("/documents", headers=bob.headers).json()["total"] == 0
    # And the owner still sees it.
    assert client.get(f"/documents/{doc_id}", headers=alice.headers).status_code == 200
