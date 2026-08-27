import os
import pickle

import faiss
import numpy as np

from dotenv import load_dotenv


load_dotenv()


DEFAULT_PATH = os.getenv(
    "VECTOR_STORE_PATH",
    "../vector_store"
)


class VectorStore:

    def __init__(
        self,
        path=DEFAULT_PATH
    ):

        self.path = path

        os.makedirs(
            self.path,
            exist_ok=True
        )

        self.index = None

        self.documents = []

        self.metadata = []

        self.load()


    def _create_index(
        self,
        dimension
    ):

        self.index = faiss.IndexFlatL2(
            dimension
        )


    def add_documents(
        self,
        embeddings,
        documents,
        metadata
    ):

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        if self.index is None:

            self._create_index(
                embeddings.shape[1]
            )

        self.index.add(
            embeddings
        )

        self.documents.extend(
            documents
        )

        self.metadata.extend(
            metadata
        )

        self.save()


    def search(
        self,
        query_embedding,
        top_k=5
    ):

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        top_k = min(
            top_k,
            self.index.ntotal
        )

        distances, indices = (
            self.index.search(
                query_embedding,
                top_k
            )
        )

        results = []

        for distance, index in zip(
            distances[0],
            indices[0]
        ):

            if index < 0:
                continue

            results.append({

                "text":
                    self.documents[index],

                "metadata":
                    self.metadata[index],

                "distance":
                    float(distance)

            })

        return results


    def save(self):

        if self.index is None:
            return

        faiss.write_index(

            self.index,

            os.path.join(
                self.path,
                "research.index"
            )

        )

        with open(

            os.path.join(
                self.path,
                "documents.pkl"
            ),

            "wb"

        ) as file:

            pickle.dump(
                self.documents,
                file
            )


        with open(

            os.path.join(
                self.path,
                "metadata.pkl"
            ),

            "wb"

        ) as file:

            pickle.dump(
                self.metadata,
                file
            )


    def load(self):

        index_path = os.path.join(
            self.path,
            "research.index"
        )

        documents_path = os.path.join(
            self.path,
            "documents.pkl"
        )

        metadata_path = os.path.join(
            self.path,
            "metadata.pkl"
        )


        if not all([

            os.path.exists(
                index_path
            ),

            os.path.exists(
                documents_path
            ),

            os.path.exists(
                metadata_path
            )

        ]):

            return


        self.index = faiss.read_index(
            index_path
        )


        with open(
            documents_path,
            "rb"
        ) as file:

            self.documents = pickle.load(
                file
            )


        with open(
            metadata_path,
            "rb"
        ) as file:

            self.metadata = pickle.load(
                file
            )