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
