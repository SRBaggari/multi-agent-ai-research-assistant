"""
Central configuration for the backend.

Everything that depends on the environment (.env) or on a file system
path is resolved here, exactly once, so the rest of the code never has
to care about the current working directory.
"""

import os

from pathlib import Path

from dotenv import load_dotenv


# --------------------------------------------------
# Project paths
# --------------------------------------------------
# __file__            -> backend/app/config.py
# .parent             -> backend/app
# .parent.parent      -> backend
# .parent.parent.parent -> project root

APP_DIR = Path(__file__).resolve().parent

BACKEND_DIR = APP_DIR.parent

PROJECT_ROOT = BACKEND_DIR.parent


# Load backend/.env no matter where uvicorn was started from.

load_dotenv(BACKEND_DIR / ".env")


def _resolve_path(raw_path: str, default: Path) -> Path:
    """
    Turn a configured path into an absolute path.

    Relative values are resolved against the PROJECT ROOT (not the
    terminal's current directory), so "../vector_store" and
    "vector_store" both end up in the same place every time.
    """

    if not raw_path:
        return default

    candidate = Path(raw_path.strip())

    if candidate.is_absolute():
        return candidate

    # "../vector_store" was written assuming the backend/ folder.
    # Normalising it against PROJECT_ROOT keeps the historic location.
    cleaned = raw_path.strip().lstrip("./")

    if cleaned.startswith("../"):
        cleaned = cleaned[3:]

    return (PROJECT_ROOT / cleaned).resolve()


# --------------------------------------------------
# OpenAI
# --------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# NOTE: this must be a model your API key can actually reach.
# "gpt-4o-mini" is cheap and available on every standard account.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


# --------------------------------------------------
# MongoDB
# --------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/").strip()

DATABASE_NAME = os.getenv("DATABASE_NAME", "research_assistant").strip()


# --------------------------------------------------
# Authentication
# --------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret").strip()

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "1"))


# --------------------------------------------------
# Storage
# --------------------------------------------------

VECTOR_STORE_PATH = _resolve_path(
    os.getenv("VECTOR_STORE_PATH", ""),
    PROJECT_ROOT / "vector_store"
)

UPLOAD_DIR = _resolve_path(
    os.getenv("UPLOAD_DIR", ""),
    BACKEND_DIR / "uploads"
)


# --------------------------------------------------
# RAG
# --------------------------------------------------

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
).strip()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))

CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))


# --------------------------------------------------
# CORS
# --------------------------------------------------

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]


# Make sure the folders exist before anything tries to write to them.

VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
