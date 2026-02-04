import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import SIMILARITY_THRESHOLD
from backend.embeddings import embed_texts
from backend.generation import generate_answer
from backend.ingestion import chunk_text, extract_text_from_pdf
from backend.query import detect_intent, transform_query
from backend.query.refusal import check_refusal
from backend.query.intent import Intent
from backend.retrieval import rerank_by_semantic
from backend.search import hybrid_search
from backend.storage import ChunkStore

app = FastAPI(
    title="rag pipeline api",
    description="retrieval-augmented generation for pdf knowledge base",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
async def query(req: QueryRequest):
    """
    query the knowledge base. 
    returns answer and source chunks.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    intent = detect_intent(question)

    if intent == Intent.GREETING:
        return {
            "answer": "Hello! I can answer questions about the documents you've uploaded. What would you like to know?",
            "sources": [],
        }

    if intent == Intent.GENERAL_CHAT:
        return {
            "answer": "I'm here to help with questions about your uploaded documents. Try asking something like 'What does this document say about X?' or 'Summarize the main points.'",
            "sources": [],
        }

    refusal = check_refusal(question)
    if refusal.should_refuse:
        return {"answer": refusal.message, "sources": []}

    # knowledge_query: run full RAG pipeline
    if not _chunks_cache:
        return {
            "answer": "No documents have been ingested yet. Please upload PDF files first.",
            "sources": [],
        }

    transformed = transform_query(question)
    try:
        query_embeddings = embed_texts([transformed])
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    query_embedding = query_embeddings[0]
    rrf_results, _ = hybrid_search(
        query_embedding, transformed, _chunks_cache, _bm25_index, top_k=20
    )

    reranked = rerank_by_semantic(rrf_results, query_embedding, _chunks_cache, top_k=5)
    if not reranked:
        return {
            "answer": "Insufficient evidence. No relevant passages were found in the knowledge base.",
            "sources": [],
        }
    best_score = reranked[0][1]
    if best_score < SIMILARITY_THRESHOLD:
        return {
            "answer": "Insufficient evidence. The retrieved passages do not meet the relevance threshold.",
            "sources": [],
        }

    context_chunks = [_chunks_cache[idx] for idx, _ in reranked]
    try:
        answer = generate_answer(question, context_chunks)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e
    sources = [
        {"source_file": c.get("source_file"), "page": c.get("page")}
        for c in context_chunks
    ]

    return {"answer": answer, "sources": sources}


@app.get("/files")
async def list_files():
    """list source filenames that have been ingested."""
    store = ChunkStore()
    chunks = store.load_chunks()
    files = sorted({c.get("source_file") for c in chunks if c.get("source_file")})
    return {"files": files}


@app.delete("/files/{filename:path}")
async def remove_file(filename: str):
    """remove all chunks for the given source file from the knowledge base."""
    store = ChunkStore()
    chunks = store.load_chunks()
    remaining = [c for c in chunks if c.get("source_file") != filename]
    if len(remaining) == len(chunks):
        raise HTTPException(status_code=404, detail=f"No ingested file named {filename!r}")
    store.replace_chunks(remaining)
    _load_index()
    return {"status": "ok", "removed": filename}


@app.get("/health")
async def health():
    """health check"""
    return {"status": "ok"}
