
import faiss
import numpy as np
from data.sample_data import SAMPLE_DATA
from app.services.base_vector_service import BaseVectorService
from app.services.text_embedding_service import TextEmbeddingService

class InMemoryVectorService(BaseVectorService):
    def __init__(self, embedding_service: TextEmbeddingService):
        self.embedding_service = embedding_service
        self.index = None
        self.data = [] # lưu raw text

    def initialize(self):
        self.build_index(SAMPLE_DATA)

    def build_index(self, texts: list[str]):
        vectors = [
            self.embedding_service.encode(text)
            for text in texts
        ]

        vectors = np.array(vectors).astype('float32')
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(vectors)

        self.data = texts

    def search(self, query: str, top_k: int = 5):
        query_vec = self.embedding_service.encode(query)
        query_vec = np.array([query_vec]).astype('float32')
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            results.append({
                'text': self.data[idx],
                'score': float(distances[0][i])
            })

        return results
