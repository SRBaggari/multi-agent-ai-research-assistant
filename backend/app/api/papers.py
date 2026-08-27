import os
import uuid

from datetime import datetime

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from app.pdf.parser import extract_pages_from_pdf
from app.pdf.chunker import create_chunks
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore
from app.database.mongodb import papers_collection


router = APIRouter(
    prefix="/papers",
    tags=["Papers"]
)


# ==================================================
# UPLOAD DIRECTORY
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ==================================================
# INITIALIZE MODELS
# ==================================================

embedding_model = EmbeddingModel()

vector_store = VectorStore()


# ==================================================
# UPLOAD PAPER
# ==================================================

@router.post("/upload")
async def upload_paper(
    file: UploadFile = File(...)
):

    # ------------------------------------------------
    # Validate filename
    # ------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )


    # ------------------------------------------------
    # Validate PDF
    # ------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )


    # ------------------------------------------------
    # Generate unique paper ID
    # ------------------------------------------------

    paper_id = str(
        uuid.uuid4()
    )


    # ------------------------------------------------
    # Create safe filename
    # ------------------------------------------------

    saved_filename = (
        f"{paper_id}.pdf"
    )


    file_path = os.path.join(
        UPLOAD_DIR,
        saved_filename
    )


    # ------------------------------------------------
    # Read uploaded file
    # ------------------------------------------------

    content = await file.read()


    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )


    # ------------------------------------------------
    # Save PDF
    # ------------------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as output_file:

            output_file.write(
                content
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save PDF: {str(error)}"
        )


    # ------------------------------------------------
    # Extract PDF pages
    # ------------------------------------------------

    try:

        pages = extract_pages_from_pdf(
            file_path
        )

    except Exception as error:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(error)}"
        )


    if not pages:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF"
        )


    # ------------------------------------------------
    # Create chunks
    # ------------------------------------------------

    try:

        chunks = create_chunks(
            pages
        )

    except Exception as error:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create text chunks: {str(error)}"
        )


    if not chunks:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="No readable text found in PDF"
        )


    # ------------------------------------------------
    # Extract chunk text
    # ------------------------------------------------

    texts = [

        chunk["text"]

        for chunk in chunks

    ]


    # ------------------------------------------------
    # Generate embeddings
    # ------------------------------------------------

    try:

        embeddings = embedding_model.encode(
            texts
        )

    except Exception as error:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embeddings: {str(error)}"
        )


    # ------------------------------------------------
    # Create metadata for every chunk
    # ------------------------------------------------

    metadata = []


    for chunk in chunks:

        metadata.append({

            "paper_id":
                paper_id,

            "filename":
                file.filename,

            "page_number":
                chunk["page_number"]

        })


    # ------------------------------------------------
    # Store vectors in FAISS
    # ------------------------------------------------

    try:

        vector_store.add_documents(

            embeddings,

            texts,

            metadata

        )

    except Exception as error:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to store embeddings: {str(error)}"
        )


    # ------------------------------------------------
    # Store paper information in MongoDB
    # ------------------------------------------------

    paper_document = {

        "paper_id":
            paper_id,

        "filename":
            file.filename,

        "stored_filename":
            saved_filename,

        "file_path":
            file_path,

        "pages":
            len(pages),

        "chunks":
            len(chunks),

        "uploaded_at":
            datetime.utcnow()

    }


    try:

        papers_collection.insert_one(
            paper_document
        )

    except Exception as error:

        print(
            f"MongoDB warning: {error}"
        )

        # We don't delete the PDF or vectors here
        # because the paper has already been processed.


    # ------------------------------------------------
    # Return response
    # ------------------------------------------------

    return {

        "message":
            "Paper uploaded successfully",

        "paper_id":
            paper_id,

        "filename":
            file.filename,

        "pages":
            len(pages),

        "chunks":
            len(chunks),

        "file_path":
            file_path

    }