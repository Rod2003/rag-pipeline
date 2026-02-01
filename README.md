## PDF Text Extraction

Text extraction uses [PyMuPDF](https://pymupdf.readthedocs.io/) with the following considerations:

- Uses `page.get_text("text")` for plain text extraction with layout awareness
- Handles password-protected and corrupt PDFs gracefully
- Preserves page order for chunking
- Strips excessive whitespace and normalizes line breaks

## Chunking Algorithm

The RAG pipeline uses a fixed-size chunking strategy with sentence-boundary awareness and overlap:

**Considerations:**
- Chunk size ~400 chars (approx 512 tokens) to fit LLM context
- Overlap ~50 chars to avoid splitting concepts across boundaries (this is a number I use for most of my RAG projects; fine tuning happens after testing phases)
- Split on sentence boundaries (. , `\n`) when possible
- Store `source_file`, `page`, `chunk_index` per chunk

## Semantic Search

Semantic search uses cosine similarity between query and chunk embeddings. No external search libraries are used:

- Uses numpy dot product on normalized vectors
- Query and chunk embeddings come from Mistral's `mistral-embed` model
- Returns top-k chunks ranked by similarity score

## Hybrid Search

The pipeline combines semantic and keyword search via **Reciprocal Rank Fusion (RRF)** to improve retrieval:

1. **Semantic search** finds chunks that are conceptually similar to the query (e.g. "cost reduction" matches "lowering expenses").
2. **Keyword search (BM25)** finds chunks that contain exact or overlapping terms (e.g. specific names, acronyms, or rare phrases).
3. **RRF merge** combines both rankings without needing to normalize or calibrate the raw scores. For each result, we compute:
   - `RRF_score(d) = Σ 1/(k + rank)` over both result lists
   - Documents that appear in both lists (or rank highly in either) receive higher RRF scores.
   - Default `k=60` balances contributions from semantic and keyword rankings.


## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.