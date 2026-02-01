import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.embeddings import embed_texts
from backend.ingestion import chunk_text, extract_text_from_pdf
from backend.storage import ChunkStore

app = FastAPI(
    title="rag pipeline api",
    description="retrieval-augmented generation for pdf knowledge base",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory index: chunks + BM25, loaded at startup / after ingest
_chunks_cache: list[dict] = []
_bm25_index = None


def _load_index():
    global _chunks_cache, _bm25_index
    store = ChunkStore()
    _chunks_cache = store.load_chunks()
    if _chunks_cache:
        from backend.search.keyword import BM25Index
        _bm25_index = BM25Index()
        _bm25_index.build(_chunks_cache)


@app.on_event("startup")
async def startup():
    _load_index()


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    """
    ingest one or more PDF files
    extracts text, chunks, embeds, and persists to storage
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    pdf_files = [f for f in files if f.filename and f.filename.lower().endswith(".pdf")]
    if not pdf_files:
        raise HTTPException(status_code=400, detail="No PDF files provided")

    store = ChunkStore()
    all_chunks: list = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for upload in pdf_files:
            path = Path(tmpdir) / upload.filename
            content = await upload.read()
            path.write_bytes(content)

            try:
                pages = extract_text_from_pdf(path)
            except (ValueError, FileNotFoundError) as e:
                raise HTTPException(status_code=400, detail=str(e)) from e

            chunks = chunk_text(pages)
            all_chunks.extend(chunks)

    texts = [c.text for c in all_chunks]
    try:
        embeddings = embed_texts(texts)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    store.save_chunks(all_chunks, embeddings=embeddings)
    _load_index()

    return {
        "status": "ok",
        "chunks_created": len(all_chunks),
        "files": [f.filename for f in pdf_files],
    }


@app.get("/health")
async def health():
    """health check"""
    return {"status": "ok"}
