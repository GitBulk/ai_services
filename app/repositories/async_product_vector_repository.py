import time
from typing import Any

from qdrant_client import models

from app.core.config import settings
from app.repositories.product_vector_base import ProductVectorBase


class AsyncProductVectorRepository(ProductVectorBase):
    async def query_multi_modal(
        self,
        text_query_vector: list[float],
        image_query_vector: list[float],
        category: str = None,
        min_price: float | None = None,
        max_price: float | None = None,
        top_k: int = 10,
    ) -> dict[str, Any]:

        query_filter = self._build_filter(category, min_price, max_price)
        prefetches = self._build_prefetches(text_query_vector, image_query_vector, query_filter, top_k)

        if not prefetches:
            return []

        start_time = time.perf_counter()

        if len(prefetches) == 1:
            results = await self._excute_single_query(prefetches[0], top_k)
        else:
            results = await self._execute_fusion_query(prefetches, top_k)

        return self._format_results(results.points, start_time)

    async def _excute_single_query(self, prefetch: models.Prefetch, top_k: int) -> models.QueryResponse:
        results = await self.qdrant_db.query_points(
            collection_name=self.current_alias_name,
            query=prefetch.query,  # Ép thẳng vào query chính
            using=prefetch.using,  # Dùng vector tương ứng
            query_filter=prefetch.filter,  # Áp filter trực tiếp
            limit=top_k,
        )
        return results

    async def _execute_fusion_query(self, prefetches: list[models.Prefetch], top_k: int) -> models.QueryResponse:
        text_weight = float(settings.TEXT_WEIGHT or 0.7)
        image_weight = float(settings.IMAGE_WEIGHT or 0.3)
        results = await self.qdrant_db.query_points(
            collection_name=self.current_alias_name,
            prefetch=prefetches,
            query=models.RrfQuery(rrf=models.Rrf(weights=[text_weight, image_weight])),
            with_payload=True,
            limit=top_k,
        )
        return results
