"""Orchestrate the full PDF ingestion pipeline."""

from uuid import uuid4

from sqlalchemy.orm import Session
from models import Document, Embedding
from .pdf_extractor import extract_text_from_pdf
from .chunker import chunk_pages
from .embedder import embed_chunks


def ingest_document(db: Session, filename: str, file_bytes: bytes) -> Document:
    """
    Full pipeline: PDF bytes → text → chunks → embeddings → database.

    Args:
        db: SQLAlchemy session
        filename: Original filename for the document record
        file_bytes: Raw PDF content

    Returns:
        The created Document record
    """
    # 1. Create document record
    document = Document(
        filename=filename,
        s3_key=f"{uuid4()}/{filename}",  # placeholder until S3 is wired up; unique per upload
        file_size=len(file_bytes),
    )
    db.add(document)
    db.flush()  # get document.id without committing

    # 2. Extract text from PDF
    pages = extract_text_from_pdf(file_bytes)

    # 3. Chunk the text
    chunks = chunk_pages(pages)

    if not chunks:
        db.commit()
        return document

    # 4. Generate embeddings
    chunks_with_embeddings = embed_chunks(chunks)

    # 5. Store embeddings
    for chunk in chunks_with_embeddings:
        embedding = Embedding(
            document_id=document.id,
            chunk_index=chunk["chunk_index"],
            text=chunk["text"],
            embedding=chunk["embedding"],
        )
        db.add(embedding)

    db.commit()
    db.refresh(document)
    return document
