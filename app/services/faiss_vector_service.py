import faiss
import pandas as pd
from app.services.base_vector_service import BaseVectorService

class FaissVectorService(BaseVectorService):
    def __init__(self, index_path, metadata_path):
        self.index = faiss.read_index(index_path)
        self.metadata = pd.read_parquet(metadata_path)

    def initialize(self):
        # load index đã làm trong __init__ rồi, nên ở đây không cần xử lý gì
        pass

    def search(self, query_vector, top_k = 5):
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            meta = self.metadata.iloc[idx].to_dict()
            meta["score"] = float(dist)
            results.append(meta)

        return results