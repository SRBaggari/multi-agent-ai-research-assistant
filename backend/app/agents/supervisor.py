"""
LangGraph supervisor.

Flow:

    START -> classifier -> (qa | comparison | gap | literature | summarizer) -> END

The supervisor only routes.  The OpenAI client lives in app/agents/llm.py
so that agents and supervisor never import each other.
"""

import os
import re

from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.agents.llm import ask_llm, LLMError

from app.agents.qa_agent import answer_question
from app.agents.comparison_agent import compare_papers
from app.agents.gap_agent import identify_research_gaps
from app.agents.literature_agent import generate_literature_review
from app.agents.summarizer import summarize_paper


# Optional: let the LLM decide when no keyword matches.
# Off by default so routing stays deterministic, fast and free.

USE_LLM_ROUTER = os.getenv(
    "USE_LLM_ROUTER",
    "false"
).strip().lower() in ("1", "true", "yes")


VALID_AGENTS = (
    "qa",
    "comparison",
    "gap",
    "literature",
    "summarizer"
)


# --------------------------------------------------
# Keyword rules
# --------------------------------------------------
# Order matters: the first group that matches wins.
# "research gap" is checked before "compare" so that a question like
# "compare the research gaps" is still treated as a gap question.

KEYWORD_RULES = [

    ("gap", [
        "research gap",
        "research gaps",
        "gaps in",
        "limitation",
        "limitations",
        "shortcoming",
        "weakness",
        "weaknesses",
        "future work",
        "future research",
        "future direction",
        "future directions",
        "open problem",
        "open problems",
        "unexplored",
        "missing from",
    ]),

    ("literature", [
        "literature review",
        "literature survey",
        "literature",
        "related work",
        "related works",
        "survey of",
        "state of the art",
        "state-of-the-art",
        "prior work",
        "background research",
    ]),

    ("comparison", [
        "compare",
        "comparison",
        "comparative",
        "contrast",
        "difference",
        "differences",
        "differ",
        "versus",
        "vs",
        "vs.",
        "better than",
        "which paper",
        "which approach",
        "side by side",
        "side-by-side",
    ]),

    ("summarizer", [
        "summary",
        "summarize",
        "summarise",
        "summarization",
        "tldr",
        "tl;dr",
        "overview",
        "abstract",
        "in short",
        "brief description",
        "key points",
        "key takeaways",
        "main points",
    ]),

]


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Whole-word phrase match.

    Prevents accidents such as "vs" matching inside "versatile"
    or "gap" matching inside "gaps-analysis-tool".
    """

    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"

    return re.search(pattern, text) is not None


def classify_by_keywords(query: str) -> str | None:
    """Return an agent name, or None when no keyword matched."""

    text = query.lower()

    for agent, phrases in KEYWORD_RULES:

        for phrase in phrases:

            if _contains_phrase(text, phrase):
                return agent

    return None


def classify_by_llm(query: str) -> str | None:
    """
    Ask the model to pick an agent.

    Returns None on any failure so that routing can fall back to QA
    instead of breaking the request.
    """

    prompt = (
        "Classify the research assistant request below into exactly one "
        "category. Reply with the category word only.\n\n"
        "Categories:\n"
        "qa          - a factual question about the paper(s)\n"
        "comparison  - comparing or contrasting papers/approaches\n"
        "gap         - research gaps, limitations or future work\n"
        "literature  - a literature review or related-work overview\n"
        "summarizer  - a summary or overview of a paper\n\n"
        f"Request: {query}\n\n"
        "Category:"
    )

    try:
        answer = ask_llm(prompt).strip().lower()

    except LLMError:
        return None

    for agent in VALID_AGENTS:
        if agent in answer:
            return agent

    return None


# --------------------------------------------------
# Graph state
# --------------------------------------------------

class ResearchState(TypedDict):

    query: str
    context: str
    result: str
    agent: str


def classify_query(state: ResearchState):
    """Decide which specialist agent should handle the request."""

    query = state.get("query", "") or ""

    agent = classify_by_keywords(query)

    if agent is None and USE_LLM_ROUTER:
        agent = classify_by_llm(query)

    if agent not in VALID_AGENTS:
        agent = "qa"

    return {"agent": agent}


# --------------------------------------------------
# Agent nodes
# --------------------------------------------------

def run_qa(state: ResearchState):
    return {
        "result": answer_question(
            state["query"],
            state["context"]
        )
    }


def run_comparison(state: ResearchState):
    return {
        "result": compare_papers(
            state["context"]
        )
    }


def run_gap(state: ResearchState):
    return {
        "result": identify_research_gaps(
            state["context"]
        )
    }


def run_literature(state: ResearchState):
    return {
        "result": generate_literature_review(
            state["context"]
        )
    }


def run_summarizer(state: ResearchState):
    return {
        "result": summarize_paper(
            state["context"]
        )
    }


def route_agent(state: ResearchState) -> str:
    return state["agent"]


# --------------------------------------------------
# Graph
# --------------------------------------------------

def build_graph():
    """Build and compile the LangGraph supervisor graph."""

    graph = StateGraph(ResearchState)

    graph.add_node("classifier", classify_query)

    graph.add_node("qa", run_qa)
    graph.add_node("comparison", run_comparison)
    graph.add_node("gap", run_gap)
    graph.add_node("literature", run_literature)
    graph.add_node("summarizer", run_summarizer)

    graph.add_edge(START, "classifier")

    graph.add_conditional_edges(
        "classifier",
        route_agent,
        {
            "qa": "qa",
            "comparison": "comparison",
            "gap": "gap",
            "literature": "literature",
            "summarizer": "summarizer",
        }
    )

    graph.add_edge("qa", END)
    graph.add_edge("comparison", END)
    graph.add_edge("gap", END)
    graph.add_edge("literature", END)
    graph.add_edge("summarizer", END)

    return graph.compile()
