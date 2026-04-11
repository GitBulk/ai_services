from typing import Any

from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class StringStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> Any:
        # data = await client.get(key)
        # if data is None:
        #     return None
        # # decode_responses=True nên data là str
        # return json.loads(data)

        return await client.get(key)

    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any):
        await client.set(key, value=value, ex=ttl)
