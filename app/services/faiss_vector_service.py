import faiss
import pandas as pd
from app.services.base_vector_service import BaseVectorService

class FaissVectorService(BaseVectorService):
    def __init__(self, resource_manager, use_cosine: bool = False):
        self.rm = resource_manager
        self.use_cosine = use_cosine

    def search(self, query_vector, top_k = 5):
        index, metadata = self.rm.resources

        if index is None:
            raise RuntimeError('Index not initialized')

        # Nếu dùng cosine similarity, cần normalize vector query
        if self.use_cosine:
            faiss.normalize_L2(query_vector)

        distances, indices = index.search(query_vector, top_k)

        # results = []
        # for idx, dist in zip(indices[0], distances[0]):
        #     meta = metadata.iloc[idx].to_dict()
        #     meta['score'] = float(dist)
        #     results.append(meta)

        # return results
        rows = metadata.iloc[indices[0]].to_dict('records')
        for row, dist in zip(rows, distances[0]):
            row["score"] = float(dist)

        return rows

    def clear_cache(self):
        pass
