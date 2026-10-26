"""Extract text from PDF files using pdfplumber."""

import pdfplumber
import io
from typing import List


def extract_text_from_pdf(file_bytes: bytes) -> List[str]:
    """
    Extract text from a PDF, returning one string per page.

    Args:
        file_bytes: Raw PDF file content

    Returns:
        List of page text strings (empty string for pages with no extractable text)
    """
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            # Postgres text columns reject NUL bytes, which some PDFs emit
            pages.append(text.replace("\x00", "").strip())
    return pages
