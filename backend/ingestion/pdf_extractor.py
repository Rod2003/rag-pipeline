import re
from pathlib import Path

import fitz


def extract_text_from_pdf(file_path: str | Path) -> list[dict]:
    """
    extracts text from a PDF file.
    raises ValueError if PDF is corrupt, encrypted, or cannot be opened.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {path}")

    try:
        doc = fitz.open(path)
    except fitz.FileDataError as e:
        raise ValueError(f"Cannot open PDF (corrupt or invalid): {e}") from e
    except fitz.FileNotFoundError as e:
        raise FileNotFoundError(str(e)) from e

    try:
        if doc.is_encrypted:
            raise ValueError("PDF is password-protected and cannot be processed")

        pages = []
        source_name = path.name

        for page_num in range(len(doc)):
            page = doc[page_num]
            raw_text = page.get_text("text")

            # normalize: strip excess whitespace, collapse multiple newlines
            text = _normalize_text(raw_text)
            if text.strip():
                pages.append({
                    "text": text,
                    "page": page_num + 1,
                    "source_file": source_name,
                })

        return pages
    finally:
        doc.close()


def _normalize_text(text: str) -> str:
    """strip excessive whitespace and normalize line breaks."""
    if not text:
        return ""
    # replace multiple whitespace with single space
    text = re.sub(r"[ \t]+", " ", text)
    # replace multiple newlines with single newline
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()
