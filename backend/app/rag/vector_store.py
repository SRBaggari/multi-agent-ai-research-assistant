"""
FAISS vector store with on-disk persistence.

Files written to VECTOR_STORE_PATH:

    research.index   - the FAISS index
    documents.pkl    - the chunk texts (same order as the index)
    metadata.pkl     - paper_id / filename / page_number per chunk

The path comes from app.config, so it is always the same folder no
matter which directory uvicorn was started from.
"""

import os
import pickle
import threading

import faiss
import numpy as np

from app.config import VECTOR_STORE_PATH


class VectorStoreError(Exception):
    """Raised when the vector store cannot be read or written."""


class VectorStore:

    def __init__(self, path=None):

        self.path = str(path or VECTOR_STORE_PATH)

        os.makedirs(self.path, exist_ok=True)

        self.index_path = os.path.join(self.path, "research.index")
        self.documents_path = os.path.join(self.path, "documents.pkl")
        self.metadata_path = os.path.join(self.path, "metadata.pkl")

        self.index = None
        self.documents = []
        self.metadata = []

        # Remembers the index file timestamp so we can notice when
        # another process wrote to the store.
        self._loaded_mtime = None

        self._lock = threading.Lock()

        self.load()

    # ----------------------------------------------
    # Basic info
    # ----------------------------------------------

    def count(self) -> int:
        """Number of chunks currently stored."""

        if self.index is None:
            return 0

        return int(self.index.ntotal)

    def is_empty(self) -> bool:
        return self.count() == 0

    def stats(self) -> dict:

        paper_ids = {
            item.get("paper_id")
            for item in self.metadata
            if item.get("paper_id")
        }

        return {
            "chunks": self.count(),
            "papers": len(paper_ids),
            "path": self.path,
        }

    # ----------------------------------------------
    # Writing
    # ----------------------------------------------

    def _create_index(self, dimension: int):
        # Embeddings are L2-normalised, so L2 distance and cosine
        # similarity rank results in the same order.
        self.index = faiss.IndexFlatL2(dimension)

    def add_documents(self, embeddings, documents, metadata):
        """Add a batch of chunks and persist the store."""

        embeddings = np.asarray(embeddings, dtype="float32")

        if embeddings.ndim != 2 or embeddings.shape[0] == 0:
            raise VectorStoreError(
                "Embeddings must be a non-empty 2D array."
            )

        if not (len(documents) == len(metadata) == embeddings.shape[0]):
            raise VectorStoreError(
                "Embeddings, documents and metadata must have the same length."
            )

        with self._lock:

            if self.index is None:
                self._create_index(embeddings.shape[1])

            if embeddings.shape[1] != self.index.d:
                raise VectorStoreError(
                    f"Embedding dimension {embeddings.shape[1]} does not match "
                    f"the existing index dimension {self.index.d}. "
                    "Delete the vector_store folder to rebuild it."
                )

            self.index.add(embeddings)

            self.documents.extend(documents)
            self.metadata.extend(metadata)

            self._save_unlocked()

    def delete_paper(self, paper_id: str) -> int:
        """
        Remove every chunk belonging to a paper.

        IndexFlatL2 keeps the raw vectors, so the surviving vectors can
        be reconstructed and written into a fresh index.  Returns the
        number of chunks removed.
        """

        with self._lock:

            if self.index is None or self.index.ntotal == 0:
                return 0

            keep = [
                position
                for position, item in enumerate(self.metadata)
                if item.get("paper_id") != paper_id
            ]

            removed = self.index.ntotal - len(keep)

            if removed == 0:
                return 0

            dimension = self.index.d

            if keep:
                vectors = np.vstack([
                    self.index.reconstruct(int(position))
                    for position in keep
                ]).astype("float32")
            else:
                vectors = None

            self._create_index(dimension)

            if vectors is not None:
                self.index.add(vectors)

            self.documents = [self.documents[position] for position in keep]
            self.metadata = [self.metadata[position] for position in keep]

            self._save_unlocked()

            return removed

    # ----------------------------------------------
    # Reading
    # ----------------------------------------------

    def list_paper_ids(self) -> list:
        """Every paper_id currently present in the index."""

        self.reload_if_changed()

        seen = []

        for item in self.metadata:
            pid = item.get("paper_id")
            if pid and pid not in seen:
                seen.append(pid)

        return seen

    def search(self, query_embedding, top_k: int = 5, paper_ids=None):
        """
        Return the top_k most similar chunks, or [] when empty.

        When paper_ids is given, only chunks belonging to those papers
        are considered. IndexFlatL2 has no metadata filter, so the whole
        index is scored and the unwanted chunks are dropped afterwards.
        That is exact, and fine for a corpus of this size.
        """

        self.reload_if_changed()

        if self.index is None or self.index.ntotal == 0:
            return []

        allowed = set(paper_ids) if paper_ids else None

        if allowed is not None and not allowed:
            return []

        query_embedding = np.asarray(query_embedding, dtype="float32")

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if query_embedding.shape[1] != self.index.d:
            raise VectorStoreError(
                "Query embedding size does not match the stored index. "
                "Delete the vector_store folder and re-upload the papers."
            )

        wanted = max(1, int(top_k))

        # Filtering needs the full ranking, because the nearest chunks
        # overall may all belong to papers the caller excluded.
        # Never ask FAISS for more neighbours than it holds.
        fetch = self.index.ntotal if allowed is not None else min(wanted, self.index.ntotal)

        distances, indices = self.index.search(query_embedding, fetch)

        results = []

        for distance, position in zip(distances[0], indices[0]):

            position = int(position)

            # FAISS returns -1 when it has fewer results than requested.
            if position < 0 or position >= len(self.documents):
                continue

            metadata = self.metadata[position]

            if allowed is not None and metadata.get("paper_id") not in allowed:
                continue

            results.append({
                "text": self.documents[position],
                "metadata": metadata,
                "distance": float(distance),
            })

            if len(results) >= wanted:
                break

        return results

    # ----------------------------------------------
    # Persistence
    # ----------------------------------------------

    def save(self):
        with self._lock:
            self._save_unlocked()

    def _save_unlocked(self):

        if self.index is None:
            return

        try:

            faiss.write_index(self.index, self.index_path)

            with open(self.documents_path, "wb") as file:
                pickle.dump(self.documents, file)

            with open(self.metadata_path, "wb") as file:
                pickle.dump(self.metadata, file)

            self._loaded_mtime = os.path.getmtime(self.index_path)

        except Exception as error:
            raise VectorStoreError(
                f"Could not save the vector store: {error}"
            ) from error

    def load(self):
        """Load the index from disk when all three files are present."""

        required = (
            self.index_path,
            self.documents_path,
            self.metadata_path,
        )

        if not all(os.path.exists(path) for path in required):
            # Nothing stored yet - an empty store is a valid state.
            return

        try:

            self.index = faiss.read_index(self.index_path)

            with open(self.documents_path, "rb") as file:
                self.documents = pickle.load(file)

            with open(self.metadata_path, "rb") as file:
                self.metadata = pickle.load(file)

            self._loaded_mtime = os.path.getmtime(self.index_path)

        except Exception as error:
            raise VectorStoreError(
                f"Could not load the vector store from {self.path}: {error}"
            ) from error

        # A truncated or mismatched store would cause wrong citations.
        if (
            self.index.ntotal != len(self.documents)
            or len(self.documents) != len(self.metadata)
        ):

            raise VectorStoreError(
                "The vector store files are inconsistent "
                f"({self.index.ntotal} vectors, "
                f"{len(self.documents)} documents, "
                f"{len(self.metadata)} metadata entries). "
                f"Delete {self.path} and re-upload the papers."
            )

    def reload_if_changed(self):
        """Re-read the store when the index file changed on disk."""

        if not os.path.exists(self.index_path):
            return

        current_mtime = os.path.getmtime(self.index_path)

        if (
            self._loaded_mtime is not None
            and current_mtime <= self._loaded_mtime
        ):
            return

        self.load()


# --------------------------------------------------
# Shared instance
# --------------------------------------------------
# Uploading and searching MUST use the same object, otherwise a paper
# uploaded through /papers/upload would be invisible to /research/ask
# until the server restarted.

_vector_store = None

_vector_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """Return the single, shared VectorStore instance."""

    global _vector_store

    if _vector_store is None:

        with _vector_store_lock:

            if _vector_store is None:
                _vector_store = VectorStore()

    return _vector_store
