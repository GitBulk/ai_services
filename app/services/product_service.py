import asyncio
from typing import Any

from qdrant_client import models

from app.core.settings import settings
from app.repositories.product_repository import ProductRepository
from app.repositories.product_vector_repository import ProductVectorRepository


class ProductService:
    def __init__(self, db_repo: ProductRepository, vector_repo: ProductVectorRepository, ai_model):
        self.db_repo = db_repo
        self.vector_repo = vector_repo
        self.ai_model = ai_model
        # vì ưu tiên search theo text hơn, nên mặc định gán trọng số text cao hơn image,
        # nhưng vẫn có thể điều chỉnh qua config nếu muốn
        self.text_weight = settings.TEXT_WEIGHT or 0.7
        self.image_weight = settings.IMAGE_WEIGHT or 0.3
        print(f"[INFO] Search using weights: Text: {self.text_weight}, Image: {self.image_weight}")

    async def search_products(self, query_text, image_url, top_k: int) -> list[dict]:
        # sinh vector truy vấn
        # (Tương lai, ghép hàm rewrite_query/translate vào đây trước khi encode)
        # query_vector = self.ai_model.encode_multimodal(text=query_text, image_url=image_url)

        text_query_vector = self.ai_model.encode_text(query_text) if query_text else None
        image_query_vector = self.ai_model.encode_image(image_url) if image_url else None

        async def fetch_text_results():
            if not text_query_vector:
                return []

            return self.vector_repo.search_text_vector(query_vector=text_query_vector, top_k=top_k * 3)

        async def fetch_image_results():
            if not image_query_vector:
                return []

            return self.vector_repo.search_image_vector(query_vector=image_query_vector, top_k=top_k * 3)

        # Fetch results from both text and image searches
        text_hits, image_hits = await asyncio.gather(fetch_text_results(), fetch_image_results())

        # Dictionary lưu điểm: { product_id: final_score }
        score_map = {}

        # Xử lý điểm Text
        for hit in text_hits:
            pid = hit["id"]
            score_map[pid] = score_map.get(pid, 0.0) + (self.text_weight * hit["score"])

        # Xử lý điểm Image
        for hit in image_hits:
            pid = hit["id"]
            score_map[pid] = score_map.get(pid, 0.0) + (self.image_weight * hit["score"])

        if not score_map:
            return []

        # Sắp xếp giảm dần theo điểm số
        sorted_items = sorted(score_map.items(), key=lambda item: item[1], reverse=True)

        # Chỉ lấy đúng số lượng top_k yêu cầu
        top_items = sorted_items[:top_k]

        # Trả về format chuẩn để Rails dễ parse
        result = [{"id": pid, "score": round(score, 4)} for pid, score in top_items]

        return result

    def search_hybrid_products(self, query_text, image_url, category, top_k: int) -> dict[str, Any]:
        text_query_vector = self.ai_model.encode_text(query_text).tolist() if query_text else None
        image_query_vector = self.ai_model.encode_image(image_url).tolist() if image_url else None
        return self.vector_repo.query_hybrid(text_query_vector, image_query_vector, category=category, top_k=top_k)

    def upsert_point(self, point_id: int, vector: list[float], payload: dict):
        self.vector_repo.upsert_point(point_id=point_id, vector=vector, payload=payload)

    def upsert_batch(self, points: list[models.PointStruct]):
        self.vector_repo.upsert_batch(points=points)

    async def sample_product(self):
        return await self.db_repo.get_by_id(469014)

    # async def hybrid_search(self, query_text: str, limit: int = 10):
    #     # Oversampling: Lấy dư dữ liệu để RRF có không gian hòa trộn
    #     # Với limit=10, chúng ta sẽ lấy 30 thằng từ mỗi bên
    #     fetch_limit = limit * 3
    #     text_query_vector = self._encode_text_to_vector(query_text)

    #     # 1. Chạy song song để tối ưu Mac M3
    #     # tasks = [
    #     #     # Gọi Qdrant (Semantic)
    #     #     self.vector_repo.query_multi_modal(text_query_vector, None, top_k=fetch_limit),
    #     #     # Gọi Postgres (Lexical/BM25) - Trả về list ID
    #     #     self.db_repo.search_full_text(query_text, limit=fetch_limit),
    #     # ]
    #     vector_results = self.vector_repo.query_multi_modal(text_query_vector, None, top_k=fetch_limit)
    #     keyword_ids = await self.db_repo.search_full_text(query_text, limit=fetch_limit)

    #     # vector_results, keyword_ids = await asyncio.gather(task1, task2)
    #     print(f"[INFO] Vector results: {vector_results}")
    #     print(f"[INFO] Keyword IDs: {keyword_ids}")
    #     # 2. Thuật toán RRF (Reciprocal Rank Fusion)
    #     k = 60
    #     rrf_scores = {}  # {product_id: total_score}

    #     # Rank từ Qdrant
    #     for rank, hit in enumerate(vector_results.get("results", []), start=1):
    #         pid = hit["id"]
    #         rrf_scores[pid] = rrf_scores.get(pid, 0) + (1.0 / (k + rank))

    #     # Rank từ Postgres
    #     for rank, pid in enumerate(keyword_ids, start=1):
    #         rrf_scores[pid] = rrf_scores.get(pid, 0) + (1.0 / (k + rank))

    #     # 3. Sắp xếp và lấy đúng số lượng 'limit' người dùng cần
    #     sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

    #     # 4. Trích xuất list ID cuối cùng để query thông tin chi tiết (nếu cần)
    #     final_ids = [item[0] for item in sorted_results]

    #     return final_ids

    def _encode_text_to_vector(self, text: str):
        return self.ai_model.encode_text(text).tolist() if text else None
