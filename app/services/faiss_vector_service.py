import faiss
import pandas as pd
from app.services.base_vector_service import BaseVectorService

class FaissVectorService(BaseVectorService):
    def __init__(self, index_path, metadata_path, use_cosine: bool = False):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = None
        self.use_cosine = use_cosine
        # simple cache
        self._cache = {}

    def initialize(self):
        print("[INFO] Loading FAISS index...")
        self.index = faiss.read_index(self.index_path)

        print("[INFO] Loading metadata...")
        self.metadata = pd.read_parquet(self.metadata_path)

    def search(self, query_vector, top_k = 5):
        # Nếu dùng cosine similarity, cần normalize vector query
        if self.use_cosine:
            faiss.normalize_L2(query_vector)

        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            meta = self.metadata.iloc[idx].to_dict()
            meta["score"] = float(dist)
            results.append(meta)

        return results

    # 🔥 HOT RELOAD
    def reload_index(self):
        print('[INFO] Reloading index...')

        new_index = faiss.read_index(self.index_path)
        new_metadata = pd.read_parquet(self.metadata_path)

        self.index = new_index
        self.metadata = new_metadata

    def clear_cache(self):
        self._cache.clear()