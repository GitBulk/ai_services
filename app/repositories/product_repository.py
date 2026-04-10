from tortoise import Tortoise

from app.models.product import Product


class ProductRepository:
    async def get_by_id(self, product_id: int) -> Product | None:
        return await Product.get_or_none(id=product_id)

    async def search_full_text(self, query: str, limit: int = 10) -> list[dict]:
        if not query.strip():
            return []

        sql = """
            WITH q AS (
                SELECT websearch_to_tsquery('simple', $1) AS query
            )
            SELECT p.id, ts_rank_cd(p.search_vector, q.query) AS score
            FROM products p, q
            WHERE p.search_vector @@ q.query
            ORDER BY score DESC
            LIMIT $2
        """
        conn = Tortoise.get_connection("default")
        # Trả về list dict và map tay
        raw_data = await conn.execute_query_dict(sql, [query, limit])
        # return [Product(**row) for row in raw_data]
        return [{"id": row["id"], "score": row["score"]} for row in raw_data]

        # async with in_transaction() as conn:
        #     raw_data = await conn.execute_query_dict(sql, [query, limit])

        # return [{"id": row["id"], "score": row["score"]} for row in raw_data]
        # await Product.get(id=1)
        # async with TortoiseContext() as ctx:
        #     return await Product.get(id=1)

    async def get_products_with_order(self, ids: list) -> list[Product]:
        return await Product.start_query().filter_in_order(ids).all()
