import json
from pathlib import Path

from backend.config import DATA_DIR
from backend.ingestion.chunker import Chunk


class ChunkStore:
    """persist chunks to JSON file"""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_path = self.data_dir / "chunks.json"

    def save_chunks(self, chunks: list[Chunk]) -> None:
        """persist chunks to disk"""
        records = [
            {
                "text": c.text,
                "source_file": c.source_file,
                "page": c.page,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    def load_chunks(self) -> list[dict]:
        """load chunks from disk"""
        if not self.chunks_path.exists():
            return []
        with open(self.chunks_path, encoding="utf-8") as f:
            return json.load(f)

    def append_chunks(self, chunks: list[Chunk]) -> None:
        """append new chunks to existing store"""
        existing = self.load_chunks()
        start_idx = len(existing)
        for i, c in enumerate(chunks):
            existing.append({
                "text": c.text,
                "source_file": c.source_file,
                "page": c.page,
                "chunk_index": start_idx + i,
            })
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
