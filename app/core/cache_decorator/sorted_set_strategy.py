from typing import Any

from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class SortedSetStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> Any:
        # Trả về list of tuples: [(member, score), ...]
        return await client.zrange(key, 0, -1, withscores=True)

    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any):
        # score_field: str | None = kwargs.get("sorted_set_score_field")

        # data = {
        #     'member1': 10.5,
        #     'member2': 20.0,
        #     'member3': 15.2
        # }
        # r.zadd('key_name', data)
        async with client.pipeline(transaction=True) as pipe:
            await pipe.zadd(key, mapping=value)
            await pipe.expire(key, ttl)
            await pipe.execute()
