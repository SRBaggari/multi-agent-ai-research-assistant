"""
Sentence-Transformer embeddings.

The model is loaded lazily and shared across the whole application.
Loading it twice would waste a few hundred megabytes of memory and add
several seconds to start-up.
"""

import threading

from app.config import EMBEDDING_MODEL_NAME


class EmbeddingError(Exception):
    """Raised when text cannot be turned into vectors."""


class EmbeddingModel:

    def __init__(self, model_name: str = None):

        self.model_name = model_name or EMBEDDING_MODEL_NAME

        self._model = None

        self._lock = threading.Lock()

    def _load(self):
        """Download / load the model the first time it is needed."""

        if self._model is not None:
            return self._model

        with self._lock:

            if self._model is None:

                try:
                    # Imported here so that start-up is not blocked by
                    # the (slow) torch import when no embedding is needed.
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self.model_name)

                except Exception as error:
                    raise EmbeddingError(
                        f"Could not load the embedding model "
                        f"'{self.model_name}': {error}"
                    ) from error

        return self._model

    def encode(self, texts):
        """Encode a list of strings into normalised numpy vectors."""

        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            raise EmbeddingError("No text was given to the embedding model.")

        model = self._load()

        try:

            return model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

        except Exception as error:
            raise EmbeddingError(
                f"Failed to generate embeddings: {error}"
            ) from error


# --------------------------------------------------
# Shared instance
# --------------------------------------------------

_embedding_model = None

_embedding_lock = threading.Lock()


def get_embedding_model() -> EmbeddingModel:
    """Return the single, shared EmbeddingModel instance."""

    global _embedding_model

    if _embedding_model is None:

        with _embedding_lock:

            if _embedding_model is None:
                _embedding_model = EmbeddingModel()

    return _embedding_model
