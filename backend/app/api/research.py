"""
Research endpoint.

    query -> retriever -> context -> LangGraph supervisor -> agent -> answer

Every failure along the way is converted into an HTTP error that
explains what actually went wrong.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel, Field

from pymongo.errors import PyMongoError

from app.api.auth import get_optional_user

from app.agents.llm import LLMError
from app.agents.supervisor import build_graph, classify_query

from app.rag.embeddings import EmbeddingError
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStoreError

from app.database.mongodb import research_collection


router = APIRouter(
    prefix="/research",
    tags=["Research"]
)


retriever = Retriever()

research_graph = build_graph()


MAX_TOP_K = 20


class ResearchQuery(BaseModel):

    query: str = Field(
        min_length=1,
        max_length=2000,
        description="The research question to ask about the uploaded papers."
    )

    top_k: int = Field(
        default=6,
        ge=1,
        le=MAX_TOP_K,
        description="How many paper chunks to use as context."
    )

    paper_ids: list[str] | None = Field(
        default=None,
        description=(
            "Limit the question to these papers. Leave it out to search "
            "every uploaded paper. Select two or more to compare them."
        )
    )


@router.post("/ask")
def ask_research_question(
    request: ResearchQuery,
    current_user: dict | None = Depends(get_optional_user),
):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="The question cannot be empty."
        )

    # ---------------------------------------------
    # 1. Is there anything to search at all?
    # ---------------------------------------------

    try:
        store_is_empty = retriever.is_empty()

    except VectorStoreError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    if store_is_empty:
        raise HTTPException(
            status_code=400,
            detail=(
                "No research papers have been uploaded yet. "
                "Upload a PDF through POST /papers/upload first."
            )
        )

    # ---------------------------------------------
    # 2. Retrieve the relevant chunks
    # ---------------------------------------------

    # Which papers is this question about?
    available = retriever.list_paper_ids()

    if request.paper_ids:
        selected = [pid for pid in request.paper_ids if pid in available]

        if not selected:
            raise HTTPException(
                status_code=404,
                detail=(
                    "None of the selected papers are in the search index. "
                    "Refresh the paper list and try again."
                )
            )
    else:
        selected = available

    # The supervisor decides the agent from the same deterministic rule,
    # so asking here does not change which agent ends up running.
    agent_hint = classify_query({"query": query}).get("agent", "qa")

    # A comparison needs material from every paper, otherwise the most
    # similar chunks can all come from one of them.
    balanced = agent_hint == "comparison" and len(selected) > 1

    try:
        if balanced:
            results = retriever.retrieve_balanced(query, request.top_k, selected)
        else:
            results = retriever.retrieve(query, request.top_k, selected)

    except EmbeddingError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    except VectorStoreError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {error}"
        ) from error

    if not results:
        raise HTTPException(
            status_code=404,
            detail=(
                "No relevant content was found in the uploaded papers "
                "for this question."
            )
        )

    # ---------------------------------------------
    # 3. Build the context and the source list
    # ---------------------------------------------

    context_parts = []

    sources = []

    for result in results:

        text = result.get("text", "")

        # .get() everywhere: a store written by an older version of the
        # app could be missing a field, and that must not cause a 500.
        metadata = result.get("metadata") or {}

        filename = metadata.get("filename", "unknown.pdf")

        page_number = metadata.get("page_number", 0)

        context_parts.append(
            f"SOURCE: {filename}\n"
            f"PAGE: {page_number}\n\n"
            f"CONTENT:\n{text}"
        )

        sources.append({
            "paper_id": metadata.get("paper_id", ""),
            "filename": filename,
            "page_number": page_number,
            "text": text,
            "score": round(result.get("distance", 0.0), 4),
        })

    context = "\n\n---\n\n".join(context_parts)

    # ---------------------------------------------
    # 4. Run the multi-agent graph
    # ---------------------------------------------

    try:

        state = research_graph.invoke({
            "query": query,
            "context": context,
            "result": "",
            "agent": "",
        })

    except LLMError as error:
        # Missing API key, wrong model name, quota, network...
        raise HTTPException(
            status_code=502,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"The multi-agent graph failed: {error}"
        ) from error

    answer = state.get("result", "")

    agent = state.get("agent", "qa")

    if not answer:
        raise HTTPException(
            status_code=502,
            detail="The agent did not return an answer."
        )

    response = {
        "query": query,
        "agent": agent,
        "answer": answer,
        "sources": sources,
        # Which papers actually contributed context, so the frontend can
        # show what the answer was based on.
        "papers_used": sorted({
            source["filename"] for source in sources if source["filename"]
        }),
    }

    # ---------------------------------------------
    # 5. Save the interaction (best effort)
    # ---------------------------------------------

    try:

        research_collection.insert_one({
            "query": query,
            "agent": agent,
            "answer": answer,
            "sources": sources,
            "user_id": (current_user or {}).get("user_id"),
            "created_at": datetime.now(timezone.utc),
        })

    except PyMongoError:
        # History is a nice-to-have; never fail the answer over it.
        pass

    return response


@router.get("/history")
def research_history(limit: int = 20):
    """Return the most recent questions and answers."""

    limit = max(1, min(limit, 100))

    try:

        documents = list(
            research_collection
            .find({}, {"_id": 0, "sources": 0})
            .sort("created_at", -1)
            .limit(limit)
        )

    except PyMongoError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not reach the database. Is MongoDB running?"
        ) from error

    for document in documents:
        created_at = document.get("created_at")
        if isinstance(created_at, datetime):
            document["created_at"] = created_at.isoformat()

    return {"count": len(documents), "history": documents}
