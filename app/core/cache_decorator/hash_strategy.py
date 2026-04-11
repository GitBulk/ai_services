from typing import Any

from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class HashStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> Any:
        return await client.hgetall(key)

    async def set(self, client: AsyncRedis, key: str, value: dict[str, Any], ttl: int, **kwargs: Any):
        async with client.pipeline(transaction=True) as pipe:
            await pipe.hset(key, mapping=value)
            await pipe.expire(key, ttl)
            return await pipe.execute()
