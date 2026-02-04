import json
from pathlib import Path

from backend.config import DATA_DIR
from backend.ingestion.chunker import Chunk


class ChunkStore:
    """persist chunks with embeddings to JSON file"""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_path = self.data_dir / "chunks.json"

    def save_chunks(self, chunks: list[Chunk], embeddings: list[list[float]] | None = None) -> None:
        """persist chunks (and optionally embeddings) to disk"""
        records = []
        for i, c in enumerate(chunks):
            rec = {
                "text": c.text,
                "source_file": c.source_file,
                "page": c.page,
                "chunk_index": c.chunk_index,
            }
            if embeddings and i < len(embeddings):
                rec["embedding"] = embeddings[i]
            records.append(rec)
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    def load_chunks(self) -> list[dict]:
        """load chunks from disk (includes embeddings if present)"""
        if not self.chunks_path.exists():
            return []
        with open(self.chunks_path, encoding="utf-8") as f:
            return json.load(f)

    def replace_chunks(self, records: list[dict]) -> None:
        """overwrite storage with a list of chunk records (e.g. after filtering)."""
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
