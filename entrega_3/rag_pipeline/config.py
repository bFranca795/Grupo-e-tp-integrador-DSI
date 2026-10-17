from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
PERSIST_PATH = PROJECT_ROOT / "chroma_db"
ORIGINAL_COLLECTION = "estudio_contable"
CHUNKS_COLLECTION = "estudio_contable_chunks"
