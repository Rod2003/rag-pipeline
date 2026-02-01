import re
from dataclasses import dataclass

from backend.config import CHUNK_OVERLAP, CHUNK_SIZE


@dataclass
class Chunk:
    text: str
    source_file: str
    page: int
    chunk_index: int


def chunk_text(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    split extracted page text into overlapping chunks. 
    overlapping is intentional to allow for retrieval of context across chunks.
    """
    chunks: list[Chunk] = []

    for page_data in pages:
        text = page_data["text"]
        source_file = page_data["source_file"]
        page = page_data["page"]

        page_chunks = _chunk_page_text(
            text=text,
            source_file=source_file,
            page=page,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        chunks.extend(page_chunks)

    # assign global chunk indices
    for i, c in enumerate(chunks):
        c.chunk_index = i

    return chunks


def _chunk_page_text(
    text: str,
    source_file: str,
    page: int,
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    """chunk a single page's text with sentence-boundary awareness"""
    if not text.strip():
        return []

    # prefer splitting on sentence boundaries
    sentences = _split_sentences(text)
    chunks: list[Chunk] = []
    current = []
    current_len = 0
    chunk_idx = 0

    for sent in sentences:
        sent_len = len(sent) + 1  # +1 for space
        if current_len + sent_len > chunk_size and current:
            chunk_text = " ".join(current).strip()
            chunks.append(
                Chunk(
                    text=chunk_text,
                    source_file=source_file,
                    page=page,
                    chunk_index=chunk_idx,
                )
            )
            chunk_idx += 1

            # overlap: keep last N chars worth of content
            overlap_text = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) + 1 <= overlap:
                    overlap_text.insert(0, s)
                    overlap_len += len(s) + 1
                else:
                    break
            current = overlap_text
            current_len = overlap_len

        current.append(sent)
        current_len += sent_len

    if current:
        chunk_text = " ".join(current).strip()
        chunks.append(
            Chunk(
                text=chunk_text,
                source_file=source_file,
                page=page,
                chunk_index=chunk_idx,
            )
        )

    return chunks


def _split_sentences(text: str, max_part_len: int = 400) -> list[str]:
    """split text into sentences, roughly on . ! ? and newlines"""
    # split on sentence-ending punctuation followed by space or newline
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    result = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) <= max_part_len:
            result.append(p)
        else:
            # fallback: split long segments by word boundaries
            words = p.split()
            current = []
            current_len = 0
            for w in words:
                if current_len + len(w) + 1 > max_part_len and current:
                    result.append(" ".join(current))
                    current = [w]
                    current_len = len(w)
                else:
                    current.append(w)
                    current_len += len(w) + (1 if current_len else 0)
            if current:
                result.append(" ".join(current))
    return result
