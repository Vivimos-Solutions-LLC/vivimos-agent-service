"""Unit tests for PDF text extraction. No PDF file or DB needed."""

from unittest.mock import MagicMock, patch

from services.pdf_extractor import extract_text_from_pdf


def _fake_pdf(page_texts):
    pages = [MagicMock(**{"extract_text.return_value": t}) for t in page_texts]
    pdf = MagicMock(pages=pages)
    pdf.__enter__.return_value = pdf
    return pdf


def test_strips_nul_bytes():
    # Regression: Postgres rejects NUL (0x00) in text columns, which crashed /ingest with a 500
    with patch("services.pdf_extractor.pdfplumber.open", return_value=_fake_pdf(["迴流\x00比 1.2Q"])):
        assert extract_text_from_pdf(b"%PDF") == ["迴流比 1.2Q"]


def test_page_without_text_becomes_empty_string():
    with patch("services.pdf_extractor.pdfplumber.open", return_value=_fake_pdf([None, "  page 2  "])):
        assert extract_text_from_pdf(b"%PDF") == ["", "page 2"]
