from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_document() -> None:
    response = client.post(
        "/documents",
        json={"title": "Test Doc", "text": "Hello world. Hello again!"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test Doc"
    assert body["insights"]["word_count"] == 4
    doc_id = body["id"]

    get_response = client.get(f"/documents/{doc_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == doc_id


def test_get_missing_document_returns_404() -> None:
    response = client.get("/documents/does-not-exist")
    assert response.status_code == 404


def test_create_document_invalid_payload_returns_422() -> None:
    response = client.post("/documents", json={"title": "", "text": "hi"})
    assert response.status_code == 422


def test_list_documents() -> None:
    response = client.get("/documents")
    assert response.status_code == 200
    body = response.json()
    assert "documents" in body
    assert "total" in body
    assert body["total"] == len(body["documents"])
