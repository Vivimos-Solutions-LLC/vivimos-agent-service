# Vivimos Agent Service

A FastAPI microservice implementing a Retrieval-Augmented Generation (RAG)
pipeline: upload a PDF, extract and chunk its text, embed the chunks into
`pgvector`, and answer natural-language questions against it via vector
similarity search + an LLM.

This is a proof-of-concept extract of a RAG pipeline built while developing
[Vivimos Solutions](https://github.com/Vivimos-Soluctions-LLC)' document-intelligence
backend, published standalone for portfolio purposes (no proprietary data,
prompts, or client-specific logic). This POC's `/chat` endpoint calls OpenAI
(`text-embedding-3-small` for retrieval, `gpt-4o` for generation) end-to-end;
an Anthropic API key/client is also wired into config for Claude-based
generation, not exercised in this POC build.

## How it works

```
PDF upload ─▶ pdfplumber extraction ─▶ overlapping text chunking
                                              │
                                              ▼
                              OpenAI text-embedding-3-small
                                              │
                                              ▼
                                  pgvector (Postgres) storage
                                              │
        query ─▶ embed query ─▶ cosine/L2 nearest-neighbor search ─▶ top-k chunks
                                              │
                                              ▼
                              LLM answers grounded in retrieved chunks
```

## Setup

### 1. Install dependencies
Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`).
```bash
uv sync  # creates .venv and installs app + dev dependencies
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your actual values:
# - DATABASE_URL (PostgreSQL with pgvector extension)
# - ANTHROPIC_API_KEY
# - OPENAI_API_KEY
```

### 3. Run tests
```bash
uv run pytest                 # fast tests: validation + error paths, no API calls
uv run pytest -m integration  # end-to-end RAG against Postgres + OpenAI (needs SAMPLE_PDF)
```

### 4. Start the server
```bash
uv run uvicorn main:app --reload
```

Server runs at `http://localhost:8000`
Docs at `http://localhost:8000/docs`

## API Endpoints

- `GET /` — Health check
- `POST /ingest` — Upload a PDF; extracts text, chunks it, generates
  embeddings, and stores everything in Postgres/pgvector. Returns the
  document record and chunk count.
- `POST /chat` — Ask a question about a previously ingested document.
  Embeds the query, retrieves the top-k nearest chunks by vector distance,
  and returns an LLM-generated answer grounded in that context.

## Project Structure

```
.
├── main.py                    # FastAPI app + route handlers
├── config.py                  # Pydantic settings from environment
├── models/
│   ├── document.py            # Document ORM model
│   └── embedding.py           # Embedding ORM model (pgvector column)
├── services/
│   ├── pdf_extractor.py       # PDF → per-page text (pdfplumber)
│   ├── chunker.py             # Text → overlapping chunks
│   ├── embedder.py            # Chunks → embeddings (OpenAI)
│   ├── ingestion.py           # Orchestrates the full ingest pipeline
│   └── chat.py                # Query → vector search → LLM answer
└── docker-compose.yml         # Local Postgres + pgvector for dev
```

## Requirements

- Python 3.12+
- PostgreSQL 13+ with the pgvector extension (or `docker compose up db`)
- Anthropic API key
- OpenAI API key

## Notes

This is a trimmed extract of a larger service — some pieces (S3-backed file
storage, auth, multi-tenant document scoping) are simplified or stubbed out
here. The RAG mechanics (extraction → chunking → embedding → retrieval →
grounded generation) are the real, working pipeline.
