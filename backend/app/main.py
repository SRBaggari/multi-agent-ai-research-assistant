"""
FastAPI application entry point.

Run from the backend/ folder with:

    python -m uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import CORS_ORIGINS, OPENAI_MODEL, OPENAI_API_KEY

from app.api.auth import router as auth_router
from app.api.papers import router as papers_router
from app.api.research import router as research_router

from app.database.mongodb import test_database, ensure_indexes

from app.rag.vector_store import get_vector_store


logger = logging.getLogger("research_assistant")


app = FastAPI(
    title="Multi-Agent AI Research Assistant",
    description=(
        "AI-powered research paper analysis "
        "using RAG and multi-agent systems."
    ),
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Routes
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(papers_router)
app.include_router(research_router)


# --------------------------------------------------
# Start-up
# --------------------------------------------------

@app.on_event("startup")
def on_startup():

    if not OPENAI_API_KEY:
        logger.warning(
            "OPENAI_API_KEY is not set - /research/ask will return an error."
        )

    if not test_database():
        logger.warning(
            "MongoDB is not reachable - authentication and the paper list "
            "will return errors until it is running."
        )
    else:
        ensure_indexes()


# --------------------------------------------------
# Catch-all error handler
# --------------------------------------------------

@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, error: Exception):
    """
    Turn an unexpected crash into a JSON error instead of an empty 500.

    The full traceback still goes to the server log, so nothing is
    silently swallowed.
    """

    logger.exception("Unhandled error on %s", request.url.path)

    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                f"Unexpected server error ({type(error).__name__}): {error}"
            )
        },
    )


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/", tags=["Health"])
def root():

    return {
        "message": "Multi-Agent AI Research Assistant API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    """Report the state of every dependency the app needs."""

    try:
        store = get_vector_store()
        vector_status = store.stats()

    except Exception as error:
        vector_status = {"error": str(error)}

    return {
        "status": "healthy",
        "database_connected": test_database(),
        # Only whether a key exists - never the key itself.
        "openai_key_configured": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL,
        "vector_store": vector_status,
    }
