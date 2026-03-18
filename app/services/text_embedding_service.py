from sentence_transformers import SentenceTransformer
import numpy as np

class TextEmbeddingService:
    def __init__(self, model):
        self.model = model

    def encode(self, text: str):
        if self.model is None:
            raise RuntimeError('Model not initialized')

        return self.model.encode(text)

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def similarity(self, sentence1: str, sentence2: str):
        vec1 = self.encode(sentence1)
        vec2 = self.encode(sentence2)
        return self.cosine_similarity(vec1, vec2)
