"""
End-to-end RAG tests against a real PDF: ingest, then ask questions.

Hits Postgres and the OpenAI API, so it's skipped by default. Run with:
    pytest -m integration
The sample PDF is not committed (client material); point SAMPLE_PDF at it.
"""

import os
from pathlib import Path

import pytest

from main import SessionLocal
from models import Document, Embedding

pytestmark = pytest.mark.integration

SAMPLE_PDF = Path(os.getenv(
    "SAMPLE_PDF",
    Path(__file__).resolve().parents[2] / "water" / "硝化液迴流泵_PLC控制與Modbus完整規格書.pdf",
))


@pytest.fixture(scope="module")
def document_id():
    if not SAMPLE_PDF.exists():
        pytest.skip(f"sample PDF not found: {SAMPLE_PDF}")

    from fastapi.testclient import TestClient
    from main import app

    response = TestClient(app).post(
        "/ingest", files={"file": (SAMPLE_PDF.name, SAMPLE_PDF.read_bytes(), "application/pdf")}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["chunks_stored"] > 0

    yield body["document_id"]

    db = SessionLocal()
    db.query(Embedding).filter(Embedding.document_id == body["document_id"]).delete()
    db.query(Document).filter(Document.id == body["document_id"]).delete()
    db.commit()
    db.close()


def ask(client, document_id, query):
    response = client.post("/chat", json={"query": query, "document_id": document_id})
    assert response.status_code == 200, response.text
    return response.json()["answer"]


def test_answers_control_rule(client, document_id):
    answer = ask(client, document_id, "缺氧池溶氧太高時，迴流比會被限制在多少？觸發條件是什麼？")
    assert "1.2" in answer
    assert "0.5" in answer
    assert "15" in answer


def test_answers_exact_table_value(client, document_id):
    answer = ask(client, document_id, "NO3_PV 的 Modbus 位址是多少？資料型態和單位是什麼？")
    assert "30201" in answer
    assert "REAL" in answer
    assert "mg/L" in answer


def test_does_not_hallucinate_missing_info(client, document_id):
    answer = ask(client, document_id, "這座水資源中心的年度預算是多少？")
    # The spec has no budget figures, so no currency amount should appear
    assert not any(token in answer for token in ["萬元", "億", "NT$", "$"])
