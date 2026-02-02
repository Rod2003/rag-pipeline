# RAG Pipeline

A Retrieval-Augmented Generation (RAG) system for querying PDF documents. Upload PDFs, ask questions, and get answers grounded in your documents with source citations.

## System Design

*diagram here*

### Architecture Overview

1. **Ingestion**: PDFs are extracted with PyMuPDF, chunked with overlap, embedded via Mistral, and stored in a file-based JSON store (no vector DB).
2. **Query**: User input passes through intent detection (greeting, chat, knowledge query), query transformation, hybrid search (semantic + BM25, merged with RRF), re-ranking, and a similarity threshold before generation.
3. **Generation**: Mistral chat completions produce answers from the retrieved context. If top chunks fall below the similarity threshold, the system returns "Insufficient evidence" without calling the LLM.

## PDF Text Extraction

Uses [PyMuPDF](https://pymupdf.readthedocs.io/):

- `page.get_text("text")` for layout-aware extraction
- Handles password-protected and corrupt PDFs
- Preserves page order
- Normalizes whitespace and line breaks

## Chunking Algorithm

Fixed-size chunks with sentence-boundary awareness:

- **Chunk size**: ~400 chars (~512 tokens)
- **Overlap**: ~50 chars
- **Boundaries**: Split on `.` `!` `?` and newlines
- **Metadata**: `source_file`, `page`, `chunk_index`

## Semantic Search

- Cosine similarity via numpy (no external search libs)
- Embeddings from Mistral `mistral-embed`
- Returns top-k by similarity

## Hybrid Search (RRF)

Combines semantic and BM25 keyword search via **Reciprocal Rank Fusion**:

- Semantic: conceptual similarity (e.g. "cost reduction" ↔ "lowering expenses")
- Keyword: exact/lexical matches (names, acronyms)
- RRF: `RRF_score(d) = Σ 1/(k + rank)` with `k=60`

## Citations & Threshold

- **Similarity threshold** (default 0.4): If the best chunk score is below this, the system returns "Insufficient evidence" and does not call the LLM.
- **Source citations**: Answers include file name and page numbers for each cited chunk.

## Query Refusal

The system refuses to process queries that:

- **PII**: Appear to contain SSN, credit card numbers, or email addresses.
- **Legal/Medical**: Request legal or medical advice, with a disclaimer to consult qualified professionals.

## How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Mistral API key](https://console.mistral.ai/)

### Backend

```bash
cd /path/to/rag-pipeline
pip install -r backend/requirements.txt
```

Create a `.env` file in the project root:

```
MISTRAL_API_KEY=your_api_key_here
```

Start the API:

```bash
PYTHONPATH=. uvicorn backend.main:app --reload --port 8000
```

Or with npm:

```bash
npm run dev:api
```

### Frontend

```bash
npm install
npm run dev:next
```

Or run both together:

```bash
npm run dev
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Upload one or more PDF files (multipart/form-data) |
| POST | `/query` | Query the knowledge base (`{"question": "..."}`) |
| GET | `/files` | List ingested source files |
| DELETE | `/files/{filename}` | Remove a file's chunks from the knowledge base |
| GET | `/health` | Health check |

## Libraries & Software

| Purpose | Library | Link |
|---------|---------|------|
| API | FastAPI | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) |
| Server | Uvicorn | [uvicorn.org](https://www.uvicorn.org/) |
| PDF | PyMuPDF | [pymupdf.readthedocs.io](https://pymupdf.readthedocs.io/) |
| LLM + Embeddings | Mistral AI | [docs.mistral.ai](https://docs.mistral.ai/) |
| Math | NumPy | [numpy.org](https://numpy.org/) |
| Frontend | Next.js | [nextjs.org](https://nextjs.org/) |
| UI | Radix UI, Tailwind | [radix-ui.com](https://radix-ui.com/), [tailwindcss.com](https://tailwindcss.com/) |
