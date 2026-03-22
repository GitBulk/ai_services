import numpy as np

class Retriever:
    def __init__(self, vector_service, text_service):
        self.vector_service = vector_service
        self.text_service = text_service

    def retrieve(self, query_text, top_k: int = 50):
        """
        Expect vector_service.search() trả về:
        [
          {"id": ..., "text": ..., "score": ..., "metadata": ...}
        ]
        """
        query_vector = self.text_service.embed(query_text)
        return self.vector_service.search(query_vector, top_k=top_k)
