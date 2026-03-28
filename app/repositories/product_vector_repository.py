import time
from typing import Any

from qdrant_client import QdrantClient, models

from app.core.settings import settings


class ProductVectorRepository:
    def __init__(self, qdrant_db: QdrantClient):
        self.qdrant_db = qdrant_db
        self.current_alias_name = f"{settings.QDRANT_ENVIRONMENT}_nova_products_alias"

    def query_similar_points(
        self,
        vector_name: str,
        query_vector: list[float],
        category: str | None,
        min_price: float | None,
        max_price: float | None,
        top_k: int = 10,
    ) -> dict[str, Any]:
        query_filter = self._build_filter(category, min_price, max_price)
        results = self.qdrant_db.query_points(
            collection_name=self.current_alias_name,
            query=models.NamedVectorStruct(name=vector_name, vector=query_vector),
            query_filter=query_filter,
            with_payload=True,
            limit=top_k,
        )
        return self._format_results(results.points)

    def query_points_with_specific_vector(
        self, vector_name: str, query_vector: list[float], top_k: int = 10
    ) -> dict[str, Any]:
        results = self.qdrant_db.query_points(
            collection_name=self.current_alias_name,
            query=models.NamedVectorStruct(name=vector_name, vector=query_vector),
            limit=top_k,
            with_payload=True,
        )
        return self._format_results(results.points)

    def query_hybrid(
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
            results = self._excute_single_query(prefetches[0], top_k)
        else:
            results = self._execute_fusion_query(prefetches, top_k)

        return self._format_results(results.points, start_time)

    def search_similar(self, query_vector: list[float], top_k: int) -> dict[str, Any]:
        results = self.qdrant_db.search(
            collection_name=self.current_alias_name,
            query_vector=query_vector,
            limit=top_k,
        )
        return self._format_results(results.points)

    def search_specific_vector(self, vector_name: str, query_vector: list[float], top_k: int) -> dict[str, Any]:
        results = self.qdrant_db.search(
            collection_name=self.current_alias_name, query_vector=(vector_name, query_vector), limit=top_k
        )
        return self._format_results(results.points)

    def search_text_vector(self, query_vector: list[float], top_k: int) -> list[dict]:
        return self.search_specific_vector("text_vector", query_vector, top_k)

    def search_image_vector(self, query_vector: list[float], top_k: int) -> list[dict]:
        return self.search_specific_vector("image_vector", query_vector, top_k)

    def upsert_point(self, point_id: int, vector: list[float], payload: dict):
        """Đẩy hàng loạt điểm"""
        point = models.PointStruct(id=point_id, vector=vector, payload=payload)
        self.qdrant_db.upsert(collection_name=self.current_alias_name, points=[point])

    def upsert_batch(self, points: list[models.PointStruct]):
        """Đẩy hàng loạt (Batch) lên Qdrant để tối ưu tốc độ mạng"""
        self.qdrant_db.upsert(collection_name=self.current_alias_name, points=points)

    def switch_alias(self, collection_name_to_switch: str, cleanup_old_collection: bool = False):
        """Switch alias sang collection mới (Blue-Green)"""
        # This action will move current alias from "old_collection" to "new_collection"
        action = models.RenameAliasOperation(
            rename_alias=models.RenameAlias(
                old_alias_name=self.current_alias_name,
                new_alias_name=self.current_alias_name,  # Alias name stays the same, its target changes
                collection_name=collection_name_to_switch,
            )
        )
        self.qdrant_db.update_collection_aliases(change_alias_operations=[action])

        if not cleanup_old_collection:
            print("Đã switch alias, không xóa collection cũ. Hãy dọn dẹp thủ công.")
            return

        # cleanup old collections
        old_collections = []
        try:
            aliases = self.qdrant_db.get_aliases().aliases
            for alias in aliases:
                if alias.alias_name == self.current_alias_name:
                    old_collections.extend(alias.collection_names)
        except Exception:
            print("[WARN] Lỗi khi tìm alias cũ để dọn dẹp.")

        for old_collection in old_collections:
            if old_collection != collection_name_to_switch:
                print(f"🧹 Đang xóa collection cũ: {old_collection}...")
                self.qdrant_db.delete_collection(collection_name=old_collection)

    def create_alias_with_collection(self, collection_name: str):
        """Tạo alias trỏ vào collection (nếu chưa có)"""
        action = models.CreateAliasOperation(
            create_alias=models.CreateAlias(collection_name=collection_name, alias_name=self.current_alias_name)
        )
        self.qdrant_db.update_collection_aliases(change_aliases_operations=[action])

    def create_collection(self, collection_name: str):
        """Tạo collection mới (nếu chưa tồn tại)"""
        if self.qdrant_db.collection_exists(collection_name):
            print(f"Collection {collection_name} đã tồn tại, bỏ qua tạo mới.")
            return

        print(f"📦 Đang tạo mới collection {collection_name}...")
        self.qdrant_db.create_collection(
            collection_name=collection_name,
            vectors_config={
                "text_vector": models.VectorParams(size=512, distance=models.Distance.COSINE),
                "image_vector": models.VectorParams(size=512, distance=models.Distance.COSINE),
            },
        )

    def cleanup_old_collections(self, collection_name_to_keep: str):
        """Dọn dẹp các collection cũ không còn được alias trỏ tới"""
        old_collections = []
        try:
            aliases = self.qdrant_db.get_aliases().aliases
            for alias in aliases:
                if alias.alias_name == self.current_alias_name:
                    old_collections.append(alias.collection_name)
        except Exception:
            print("[WARN] Lỗi khi tìm alias cũ để dọn dẹp.")

        for old_collection in old_collections:
            if old_collection != collection_name_to_keep:
                print(f"🧹 Đang xóa collection cũ: {old_collection}...")
                self.qdrant_db.delete_collection(collection_name=old_collection)

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

    def _excute_single_query(self, prefetch: models.Prefetch, top_k: int) -> models.QueryResponse:
        results = self.qdrant_db.query_points(
            collection_name=self.current_alias_name,
            query=prefetch.query,  # Ép thẳng vào query chính
            using=prefetch.using,  # Dùng vector tương ứng
            query_filter=prefetch.filter,  # Áp filter trực tiếp
            limit=top_k,
        )
        return results

    def _execute_fusion_query(self, prefetches: list[models.Prefetch], top_k: int) -> models.QueryResponse:
        text_weight = float(settings.TEXT_WEIGHT or 0.7)
        image_weight = float(settings.IMAGE_WEIGHT or 0.3)
        results = self.qdrant_db.query_points(
            collection_name=self.current_alias_name,
            prefetch=prefetches,
            query=models.RrfQuery(rrf=models.Rrf(weights=[text_weight, image_weight])),
            with_payload=True,
            limit=top_k,
        )
        return results

    def _format_results(self, points, start_time: float | None = None):
        metadata = {"total_hits": len(points)}
        if start_time is not None:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            metadata["elapsed_time_ms"] = round(elapsed_ms, 2)

        data = [{"id": point.id, "score": round(float(point.score), 4), **(point.payload or {})} for point in points]
        return {"results": data, "metadata": metadata}
