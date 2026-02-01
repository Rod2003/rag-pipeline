import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = BASE_DIR / "data"

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Chunking defaults
CHUNK_SIZE = 400  # ~512 tokens
CHUNK_OVERLAP = 50  # ~50 tokens
