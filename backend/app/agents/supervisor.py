import os

from typing import TypedDict

from dotenv import load_dotenv
from openai import OpenAI

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.agents.qa_agent import answer_question
from app.agents.comparison_agent import compare_papers
from app.agents.gap_agent import identify_research_gaps
from app.agents.literature_agent import generate_literature_review


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


def ask_llm(prompt: str):

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return response.output_text


class ResearchState(TypedDict):

    query: str
    context: str
    result: str
    agent: str


def classify_query(state: ResearchState):

    query = state["query"].lower()

    if "compare" in query:
        agent = "comparison"

    elif (
        "research gap" in query
        or "research gaps" in query
        or "future research" in query
    ):
        agent = "gap"

    elif (
        "literature review" in query
        or "literature" in query
    ):
        agent = "literature"

    else:
        agent = "qa"

    return {
        "agent": agent
    }


def run_qa(state: ResearchState):

    result = answer_question(
        state["query"],
        state["context"]
    )

    return {
        "result": result
    }


def run_comparison(state: ResearchState):

    result = compare_papers(
        state["context"]
    )

    return {
        "result": result
    }


def run_gap(state: ResearchState):

    result = identify_research_gaps(
        state["context"]
    )

    return {
        "result": result
    }


def run_literature(state: ResearchState):

    result = generate_literature_review(
        state["context"]
    )

    return {
        "result": result
    }


def route_agent(state: ResearchState):

    return state["agent"]


def build_graph():

    graph = StateGraph(ResearchState)

    graph.add_node(
        "classifier",
        classify_query
    )

    graph.add_node(
        "qa",
        run_qa
    )

    graph.add_node(
        "comparison",
        run_comparison
    )

    graph.add_node(
        "gap",
        run_gap
    )

    graph.add_node(
        "literature",
        run_literature
    )

    graph.add_edge(
        START,
        "classifier"
    )

    graph.add_conditional_edges(
        "classifier",
        route_agent,
        {
            "qa": "qa",
            "comparison": "comparison",
            "gap": "gap",
            "literature": "literature"
        }
    )

    graph.add_edge("qa", END)
    graph.add_edge("comparison", END)
    graph.add_edge("gap", END)
    graph.add_edge("literature", END)

    return graph.compile()