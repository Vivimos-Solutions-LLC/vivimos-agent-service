"""Request validation and error paths. No OpenAI calls."""


def test_root_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_ingest_rejects_non_pdf(client):
    response = client.post("/ingest", files={"file": ("photo.jpg", b"not a pdf", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported"


def test_ingest_rejects_empty_file(client):
    response = client.post("/ingest", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_chat_unknown_document_returns_404(client):
    response = client.post("/chat", json={"query": "hi", "document_id": 999999})
    assert response.status_code == 404


def test_chat_missing_document_id_returns_422(client):
    response = client.post("/chat", json={"query": "hi"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "document_id"]
