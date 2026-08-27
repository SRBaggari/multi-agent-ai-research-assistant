from app.rag.embeddings import EmbeddingModel

from app.rag.vector_store import VectorStore


class Retriever:

    def __init__(self):

        self.embedding_model = (
            EmbeddingModel()
        )

        self.vector_store = (
            VectorStore()
        )

    def retrieve(
        self,
        query,
        top_k=5
    ):

        query_embedding = (
            self.embedding_model.encode(
                [query]
            )
        )

        results = (
            self.vector_store.search(
                query_embedding,
                top_k
            )
        )

        return results