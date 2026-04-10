import time
from abc import ABC, abstractmethod
from typing import Any

from qdrant_client import AsyncQdrantClient, QdrantClient, models

from app.core.config import settings


class ProductVectorBase(ABC):
    def __init__(self, qdrant_db: QdrantClient | AsyncQdrantClient):
        self.qdrant_db = qdrant_db
        self.current_alias_name = f"{settings.APP_ENV}_nova_products_alias"

    @abstractmethod
    def query_multi_modal(
        self,
        text_query_vector: list[float],
        image_query_vector: list[float],
        top_k: int = 10,
        **kwargs,  # Dùng cho các filter linh hoạt như category, price...
    ) -> dict[str, Any]:
        """Subclass phải tự implement logic search (Sync/Async)"""
        pass

    @abstractmethod
    async def upsert_batch(self, points: list[models.PointStruct]) -> Any:
        """Subclass phải tự implement logic đẩy data"""
        pass

    # --- Shared Logic (Pure methods) ---
    def _build_filter(
        self, category: str | None, min_price: float | None, max_price: float | None
    ) -> models.Filter | None:
        must_conditions = []
        if category:
            must_conditions.append(
                models.FieldCondition(key="master_category", match=models.MatchValue(value=category))
            )

        if min_price is not None or max_price is not None:
            range_params = {key: value for key, value in [("gte", min_price), ("lte", max_price)] if value is not None}
            must_conditions.append(models.FieldCondition(key="price", range=models.Range(**range_params)))

        return models.Filter(must=must_conditions) if must_conditions else None

    def _build_prefetches(
        self,
        text_query_vector: list[float] | None,
        image_query_vector: list[float] | None,
        query_filter: models.Filter | None,
        top_k: int,
    ) -> list[models.Prefetch]:
        prefetches = []
        if text_query_vector:
            prefetches.append(
                models.Prefetch(query=text_query_vector, using="text_vector", limit=top_k * 3, filter=query_filter)
            )

        if image_query_vector:
            prefetches.append(
                models.Prefetch(query=image_query_vector, using="image_vector", limit=top_k * 3, filter=query_filter)
            )

        return prefetches

    def _format_results(self, points, start_time: float | None = None):
        metadata = {"total_hits": len(points)}
        if start_time is not None:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            metadata["elapsed_time_ms"] = round(elapsed_ms, 2)

        data = [{"id": point.id, "score": round(float(point.score), 4), **(point.payload or {})} for point in points]
        return {"results": data, "metadata": metadata}
