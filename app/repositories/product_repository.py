from app.models.product import Product


class ProductRepository:
    async def get_by_id(self, product_id: int) -> Product | None:
        return await Product.get_or_none(id=product_id)

    # async def search_full_text(self, query: str, limit: int = 10) -> list[dict]:
    async def search_full_text(self, query: str, limit: int = 10):
        if not query.strip():
            return []
        print("[DEBUG] search_full_text called")
        # conn = Tortoise.get_connection("default")
        # sql = """
        #     SELECT *,
        #            ts_rank_cd(search_vector, websearch_to_tsquery('english', $1)) as score
        #     FROM products
        #     WHERE search_vector @@ websearch_to_tsquery('english', $1)
        #     ORDER BY score DESC
        #     LIMIT $2
        # """
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
        # Trả về list dict và map tay
        # raw_data = await conn.execute_query_dict(sql, [query, limit])
        # return [Product(**row) for row in raw_data]

        # async with in_transaction() as conn:
        #     raw_data = await conn.execute_query_dict(sql, [query, limit])

        # return [{"id": row["id"], "score": row["score"]} for row in raw_data]
        # await Product.get(id=1)
        # async with TortoiseContext() as ctx:
        #     return await Product.get(id=1)

        return await Product.get(id=1)
