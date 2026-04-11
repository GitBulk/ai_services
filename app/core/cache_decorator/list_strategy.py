from typing import Any

from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class ListStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> list:
        return await client.lrange(key, 0, -1)

    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any) -> Any:
        async with client.pipeline(transaction=True) as pipe:
            if isinstance(value, (list, tuple)):
                await pipe.rpush(key, *value)
            else:
                await pipe.rpush(key, value)
            await pipe.expire(key, ttl)
            return await pipe.execute()
