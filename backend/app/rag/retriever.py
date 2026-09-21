"""
Retrieval step of the RAG pipeline.

query -> embedding -> FAISS search -> relevant chunks (with metadata)
"""

import math

from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import get_vector_store


class Retriever:

    def __init__(self):
        # Both of these are shared singletons, so a paper uploaded
        # through /papers/upload is immediately searchable here.
        self.embedding_model = get_embedding_model()

        self.vector_store = get_vector_store()

    def is_empty(self) -> bool:
        """True when no paper has been indexed yet."""

        self.vector_store.reload_if_changed()

        return self.vector_store.is_empty()

    def list_paper_ids(self) -> list:
        """Papers currently available to search."""

        return self.vector_store.list_paper_ids()

    def retrieve(self, query: str, top_k: int = 5, paper_ids=None):
        """
        Return the most relevant chunks for a query.

        paper_ids limits the search to those papers; None searches all.
        """

        if not query or not query.strip():
            return []

        query_embedding = self.embedding_model.encode([query])

        return self.vector_store.search(query_embedding, top_k, paper_ids)

    def retrieve_balanced(self, query: str, top_k: int, paper_ids):
        """
        Retrieve a fair share of chunks from EVERY given paper.

        A plain similarity search can return every chunk from a single
        paper, which makes a comparison impossible. This takes roughly
        top_k / number-of-papers from each paper instead, so the agent
        always sees something from all of them.
        """

        if not query or not query.strip() or not paper_ids:
            return []

        query_embedding = self.embedding_model.encode([query])

        per_paper = max(1, math.ceil(top_k / len(paper_ids)))

        collected = []

        for paper_id in paper_ids:
            collected.extend(
                self.vector_store.search(
                    query_embedding,
                    per_paper,
                    [paper_id],
                )
            )

        # Best matches first, regardless of which paper they came from.
        collected.sort(key=lambda item: item["distance"])

        return collected
