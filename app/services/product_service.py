import asyncio
import json
from typing import Any

from qdrant_client import models

from app.core.config import settings
from app.repositories.async_product_vector_repository import AsyncProductVectorRepository
from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, db_repo: ProductRepository, vector_repo: AsyncProductVectorRepository, ai_model, llm_service):
        self.db_repo = db_repo
        self.vector_repo = vector_repo
        self.ai_model = ai_model
        self.llm_service = llm_service
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

    def search_products_with_multi_modal(self, query_text, image_url, category, top_k: int) -> dict[str, Any]:
        text_query_vector = self.ai_model.encode_text(query_text).tolist() if query_text else None
        image_query_vector = self.ai_model.encode_image(image_url).tolist() if image_url else None
        return self.vector_repo.query_multi_modal(text_query_vector, image_query_vector, category=category, top_k=top_k)

    def upsert_point(self, point_id: int, vector: list[float], payload: dict):
        self.vector_repo.upsert_point(point_id=point_id, vector=vector, payload=payload)

    def upsert_batch(self, points: list[models.PointStruct]):
        self.vector_repo.upsert_batch(points=points)

    async def sample_product(self):
        return await self.db_repo.get_by_id(469014)

    async def hybrid_search(self, query_text: str, limit: int = 10):
        # Oversampling: Lấy dư dữ liệu để RRF có không gian hòa trộn
        # Với limit=10, chúng ta sẽ lấy 30 thằng từ mỗi bên
        fetch_limit = limit * 3
        text_query_vector = self._encode_text_to_vector(query_text)

        # 1. Chạy song song để tối ưu Mac M3
        vector_task = self.vector_repo.query_multi_modal(text_query_vector, None, top_k=fetch_limit)
        keyword_task = self.db_repo.search_full_text(query_text, limit=fetch_limit)
        vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)

        k = 60
        rrf_scores = {}  # {product_id: total_score}

        # Note: hiện tại, vector và text đều có trọng số bằng nhau
        # 0 < weight < 1
        # Rank từ Qdrant
        vector_weight = 1
        for rank, hit in enumerate(vector_results.get("results", []), start=1):
            pid = str(hit["id"])
            score = (1.0 / (k + rank)) * vector_weight
            rrf_scores[pid] = rrf_scores.get(pid, 0) + score

        # Rank từ Postgres
        # db_results: [{'id': 432534, 'score': 1.25}, {'id': 466692, 'score': 1.25}]
        text_weight = 1
        for rank, hit in enumerate(keyword_results, start=1):
            pid = str(hit["id"])
            score = (1.0 / (k + rank)) * text_weight
            rrf_scores[pid] = rrf_scores.get(pid, 0) + score

        # 3. Sắp xếp và lấy đúng số lượng 'limit' người dùng cần
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        print(f"[INFO] Sorted results: {sorted_results}")
        # 4. Trích xuất list ID cuối cùng để query thông tin chi tiết (nếu cần)
        final_ids = [item[0] for item in sorted_results]
        print(f"[INFO] Final IDs: {final_ids}")
        return final_ids

    async def rag_search(self, query_text: str, limit: int = 5):
        ctx = await self._build_rag_context(query_text, limit)
        if ctx is None:
            return {}

        products, system_prompt, user_prompt = ctx
        explanation = await self.llm_service.chat(
            system_message=system_prompt, user_message=user_prompt, temperature=0.3
        )
        return {"answer": explanation, "products": products}

    async def rag_search_stream(self, query_text: str, limit: int = 5):
        ctx = await self._build_rag_context(query_text, limit)
        if ctx is None:
            return

        products, system_prompt, user_prompt = ctx

        # 5. Yield full product list first so the client gets data before LLM starts
        # The products are Tortoise ORM objects with a DecimalField for price — not JSON-serializable directly.
        product_list = [
            {
                "id": p.id,
                "product_display_name": p.product_display_name,
                "price": float(p.price) if p.price is not None else None,
                "brand": p.brand,
                "image_path": p.image_path,
                "master_category": p.master_category,
                "sub_category": p.sub_category,
                "base_colour": p.base_colour,
            }
            for p in products
        ]
        yield json.dumps({"type": "products", "products": product_list}) + "\n"

        # 6. Stream LLM response
        async for chunk in self.llm_service.chat_stream(
            system_message=system_prompt, user_message=user_prompt, temperature=0.3
        ):
            yield json.dumps({"type": "chunk", "content": chunk}) + "\n"

    def _encode_text_to_vector(self, text: str):
        return self.ai_model.encode_text(text).tolist() if text else None

    async def _build_rag_context(self, query_text: str, limit: int):
        """Shared retrieval + prompt-building for rag_search and rag_search_stream.

        Returns (products, system_prompt, user_prompt) or None if no results.
        """
        final_ids = await self.hybrid_search(query_text, limit=limit)
        if not final_ids:
            return None

        products = await self.db_repo.get_products_with_order(final_ids)

        context_items = []
        for idx, p in enumerate(products, 1):
            context_items.append(
                f"Product #{idx} (ID: {p.id}):\n"
                f"- Name: {p.product_display_name}\n"
                f"- Price: {p.price}\n"
                f"- Description: {p.text_for_ai}\n"
                f"- Specs: {p.get('specs', 'N/A')}"
            )
        context_str = "\n\n".join(context_items)

        system_prompt = (
            "You are an expert product consultant for NOVA AI. "
            "Analyze the provided product context and explain their relevance to the user's query. "
            "Must strictly adhere to the provided data. Do not hallucinate."
        )

        user_prompt = f"""
    User Query: "{query_text}"

    Context (Ranked by relevance):
    {context_str}

    Instructions:
    1. Briefly summarize why these products match the user's need.
    2. Recommend the best option and provide a concise justification.
    3. If no product strictly matches, clearly state so.
    """

        return products, system_prompt, user_prompt
