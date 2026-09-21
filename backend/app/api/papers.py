"""
Paper management.

    POST   /papers/upload        upload + index a PDF
    GET    /papers               list uploaded papers
    GET    /papers/{paper_id}    details for one paper
    DELETE /papers/{paper_id}    remove a paper, its chunks and its file
"""

import os
import uuid

from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
)

from pymongo.errors import PyMongoError

from app.config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP

from app.api.auth import get_optional_user

from app.pdf.parser import extract_pages_from_pdf
from app.pdf.chunker import create_chunks

from app.rag.embeddings import get_embedding_model, EmbeddingError
from app.rag.vector_store import get_vector_store, VectorStoreError

from app.database.mongodb import papers_collection


router = APIRouter(
    prefix="/papers",
    tags=["Papers"]
)


UPLOAD_DIR = str(UPLOAD_DIR)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024   # 50 MB


def _paper_response(document: dict) -> dict:
    """Shape a MongoDB paper document for the API (drops _id)."""

    uploaded_at = document.get("uploaded_at")

    return {
        "paper_id": document.get("paper_id"),
        "filename": document.get("filename"),
        "pages": document.get("pages", 0),
        "chunks": document.get("chunks", 0),
        "uploaded_at": (
            uploaded_at.isoformat()
            if isinstance(uploaded_at, datetime)
            else uploaded_at
        ),
    }


# ==================================================
# UPLOAD PAPER
# ==================================================

@router.post("/upload")
async def upload_paper(
    file: UploadFile = File(...),
    current_user: dict | None = Depends(get_optional_user),
):

    # ------------------------------------------------
    # Validate the file
    # ------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="The PDF is larger than the 50 MB limit."
        )

    # A real PDF always starts with "%PDF".
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="This file is not a valid PDF."
        )

    # ------------------------------------------------
    # Save the PDF under a unique id
    # ------------------------------------------------

    paper_id = str(uuid.uuid4())

    file_path = os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")

    try:
        with open(file_path, "wb") as output_file:
            output_file.write(content)

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save the PDF: {error}"
        ) from error

    def cleanup():
        """Remove the saved file when indexing fails."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    # ------------------------------------------------
    # Extract text page by page
    # ------------------------------------------------

    try:
        pages = extract_pages_from_pdf(file_path)

    except Exception as error:
        cleanup()
        raise HTTPException(
            status_code=400,
            detail=f"Could not read the PDF: {error}"
        ) from error

    if not pages:
        cleanup()
        raise HTTPException(
            status_code=400,
            detail=(
                "No text could be extracted from this PDF. "
                "Scanned or image-only PDFs are not supported."
            )
        )

    # ------------------------------------------------
    # Chunk the text (page numbers are preserved)
    # ------------------------------------------------

    chunks = create_chunks(
        pages,
        chunk_size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP
    )

    if not chunks:
        cleanup()
        raise HTTPException(
            status_code=400,
            detail="No readable text was found in this PDF."
        )

    texts = [chunk["text"] for chunk in chunks]

    # ------------------------------------------------
    # Embed the chunks
    # ------------------------------------------------

    try:
        embeddings = get_embedding_model().encode(texts)

    except EmbeddingError as error:
        cleanup()
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    # ------------------------------------------------
    # Store vectors + metadata in FAISS
    # ------------------------------------------------

    metadata = [
        {
            "paper_id": paper_id,
            "filename": file.filename,
            "page_number": chunk["page_number"],
        }
        for chunk in chunks
    ]

    try:
        get_vector_store().add_documents(embeddings, texts, metadata)

    except VectorStoreError as error:
        cleanup()
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    # ------------------------------------------------
    # Record the paper in MongoDB
    # ------------------------------------------------

    paper_document = {
        "paper_id": paper_id,
        "filename": file.filename,
        "stored_filename": f"{paper_id}.pdf",
        "file_path": file_path,
        "pages": len(pages),
        "chunks": len(chunks),
        "uploaded_at": datetime.now(timezone.utc),
        "uploaded_by": (current_user or {}).get("user_id"),
    }

    database_warning = None

    try:
        papers_collection.insert_one(paper_document)

    except PyMongoError as error:
        # The paper is already indexed and searchable, so this is a
        # warning rather than a failure - but we do not hide it.
        database_warning = (
            "The paper was indexed but could not be saved to MongoDB "
            f"({type(error).__name__}). It will not appear in GET /papers."
        )

    response = {
        "message": "Paper uploaded successfully",
        **_paper_response(paper_document),
    }

    if database_warning:
        response["warning"] = database_warning

    return response


# ==================================================
# LIST PAPERS
# ==================================================

@router.get("")
@router.get("/")
def list_papers():
    """Return every uploaded paper, newest first."""

    try:
        documents = list(
            papers_collection
            .find({}, {"_id": 0})
            .sort("uploaded_at", -1)
        )

    except PyMongoError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not reach the database. Is MongoDB running?"
        ) from error

    return {
        "count": len(documents),
        "papers": [_paper_response(document) for document in documents],
    }


# ==================================================
# PAPER DETAILS
# ==================================================

@router.get("/{paper_id}")
def get_paper(paper_id: str):

    try:
        document = papers_collection.find_one(
            {"paper_id": paper_id},
            {"_id": 0}
        )

    except PyMongoError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not reach the database. Is MongoDB running?"
        ) from error

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Paper not found."
        )

    return _paper_response(document)


# ==================================================
# DELETE PAPER
# ==================================================

@router.delete("/{paper_id}")
def delete_paper(paper_id: str):
    """
    Delete a paper: its chunks are removed from FAISS, its record from
    MongoDB and its PDF from disk.
    """

    # The database lookup is best effort: a paper that was indexed while
    # MongoDB was down must still be removable from the index.
    database_available = True

    try:
        document = papers_collection.find_one({"paper_id": paper_id})

    except PyMongoError:
        document = None
        database_available = False

    store = get_vector_store()

    store.reload_if_changed()

    known_to_store = any(
        item.get("paper_id") == paper_id
        for item in store.metadata
    )

    if not document and not known_to_store:
        raise HTTPException(
            status_code=404,
            detail="Paper not found."
        )

    try:
        removed_chunks = store.delete_paper(paper_id)

    except VectorStoreError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    try:
        papers_collection.delete_one({"paper_id": paper_id})

    except PyMongoError:
        pass

    file_path = (document or {}).get(
        "file_path",
        os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")
    )

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    response = {
        "message": "Paper deleted",
        "paper_id": paper_id,
        "removed_chunks": removed_chunks,
    }

    if not database_available:
        response["warning"] = (
            "The chunks were removed from the index, but MongoDB could not "
            "be reached, so the paper record may still exist."
        )

    return response
