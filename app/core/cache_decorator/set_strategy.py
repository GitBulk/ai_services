from typing import Any

from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class SetStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> Any:
        return await client.smembers(key)

    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any):
        if not isinstance(value, (set, list, tuple)):
            value = [value]

        async with client.pipeline(transaction=True) as pipe:
            await pipe.sadd(key, *value)
            await pipe.expire(key, ttl)
            await pipe.execute()
