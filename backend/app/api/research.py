from fastapi import APIRouter

from pydantic import BaseModel

from app.rag.retriever import Retriever

from app.agents.supervisor import (
    build_graph
)


router = APIRouter(
    prefix="/research",
    tags=["Research"]
)


retriever = Retriever()

research_graph = build_graph()


class ResearchQuery(BaseModel):

    query: str

    top_k: int = 6


@router.post("/ask")
def ask_research_question(
    request: ResearchQuery
):

    # ---------------------------------------------
    # Retrieve relevant chunks
    # ---------------------------------------------

    results = retriever.retrieve(
        request.query,
        request.top_k
    )

    # ---------------------------------------------
    # Build context
    # ---------------------------------------------

    context_parts = []

    sources = []

    for result in results:

        text = result["text"]

        metadata = result["metadata"]

        filename = metadata[
            "filename"
        ]

        page_number = metadata[
            "page_number"
        ]

        context_parts.append(
            f"""
SOURCE:
{filename}
PAGE:
{page_number}

CONTENT:
{text}
"""
        )

        sources.append({

            "paper_id":
                metadata["paper_id"],

            "filename":
                filename,

            "page_number":
                page_number,

            "text":
                text

        })

    context = "\n\n".join(
        context_parts
    )

    # ---------------------------------------------
    # Run multi-agent graph
    # ---------------------------------------------

    result = research_graph.invoke({

        "query":
            request.query,

        "context":
            context,

        "result":
            "",

        "agent":
            ""

    })

    return {

        "query":
            request.query,

        "agent":
            result["agent"],

        "answer":
            result["result"],

        "sources":
            sources

    }