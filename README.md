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