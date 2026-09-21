"""
Retrieval step of the RAG pipeline.

query -> embedding -> FAISS search -> relevant chunks (with metadata)
"""

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

    def retrieve(self, query: str, top_k: int = 5):
        """Return the most relevant chunks for a query."""

        if not query or not query.strip():
            return []

        query_embedding = self.embedding_model.encode([query])

        return self.vector_store.search(query_embedding, top_k)
