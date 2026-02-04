# RAG Pipeline

A Retrieval-Augmented Generation (RAG) system for querying PDF documents. Upload PDFs, ask questions, and get answers grounded in your documents with source citations.

## System Design

<img width="3775" height="4980" alt="rag-pipeline-diagram" src="https://github.com/user-attachments/assets/a08ce94d-7cb4-4dc1-be3a-0abff086719a" />

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

---

## Code Structure & Implementation

This section maps the system design to the codebase and notes design choices made in the implementation.

### Backend Layout

| Area | Path | Role |
|------|------|------|
| API & orchestration | `backend/main.py` | FastAPI app, CORS, ingest/query/files/health routes; in-memory chunk cache and BM25 index; startup/ingest reload index from disk. |
| Config | `backend/config.py` | `.env` loaded from project root; `DATA_DIR`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `SIMILARITY_THRESHOLD`, `MISTRAL_API_KEY`. |
| Ingestion | `backend/ingestion/` | `pdf_extractor.py`: PyMuPDF extraction, validation, text normalization. `chunker.py`: `Chunk` dataclass; sentence-boundary chunking with overlap. |
| Embeddings | `backend/embeddings/mistral_client.py` | Mistral `mistral-embed`; batches of 32 for reliability. |
| Search | `backend/search/` | `semantic.py`: cosine similarity (NumPy). `keyword.py`: in-memory BM25 (`k1=1.5`, `b=0.75`). `hybrid.py`: RRF merge (`k=60`), top-k 20. |
| Retrieval | `backend/retrieval/rerank.py` | Re-ranks RRF results by semantic score; returns top-5. |
| Query pipeline | `backend/query/` | `intent.py`: rule-based greeting / general_chat / knowledge_query. `refusal.py`: PII regex + legal/medical keywords. `transform.py`: acronym expansion + definition-style query rewrites. |
| Generation | `backend/generation/llm.py` | Mistral chat (`mistral-small-latest`), single RAG prompt, `temperature=0.2`; context formatted with `[file p.N]: text`. |
| Storage | `backend/storage/store.py` | Single JSON file (`backend/data/chunks.json`); save/load/replace chunk records with optional embeddings. |

### Design Considerations

- **In-memory index**: Chunks and BM25 are kept in process and reloaded on startup and after every ingest or file delete. This avoids a vector DB and keeps the stack simple; scale limits are process memory and single-file JSON write throughput.
- **Query flow order**: Intent is resolved first (greeting → canned reply; general_chat → redirect; else knowledge path). Refusal runs only for knowledge-style queries. Then query transform, hybrid search, rerank, threshold check, and finally generation. This order avoids calling the embedding/LLM APIs for greetings or refused queries.
- **Chunking**: Sentences are split on `.!?` and newlines; long segments are split by words with a max part length. Overlap is implemented by carrying the last few sentences into the next chunk so that span boundaries are less likely to cut mid-context.
- **Hybrid search**: Semantic and BM25 each return top-20; RRF merges ranks with `k=60`. Rerank then uses semantic similarity only over that merged set and keeps top-5, so keyword hits can “boost” a doc into the rerank pool.
- **Similarity threshold**: Applied after rerank. If the best reranked chunk score is below `SIMILARITY_THRESHOLD` (0.4), the API returns “Insufficient evidence” and does not call the LLM, reducing cost and hallucination risk.
- **File list and delete**: `GET /files` derives the list of ingested source files from chunk metadata. `DELETE /files/{filename}` filters out chunks with that `source_file`, writes the remaining records via `ChunkStore.replace_chunks`, then reloads the in-memory index so subsequent queries see the update.
- **Frontend**: Next.js app in `app/page.tsx`; `API_BASE` from `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Chat state is local (no backend session). Ingested files are listed from `GET /files`; remove calls `DELETE /files/{filename}`. Assistant answers are rendered as Markdown; sources are grouped by file and shown as an accordion with page badges.

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
