import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Chunking defaults
CHUNK_SIZE = 400  # ~512 tokens
CHUNK_OVERLAP = 50  # ~50 tokens
