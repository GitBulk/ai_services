from typing import Any

import numpy as np
from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class VectorStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> Any:
        data = await client.get(key)
        if data is None:
            return None

        try:
            # data là str (hex) → chuyển về bytes
            vector_bytes = bytes.fromhex(data)
            return np.frombuffer(vector_bytes, dtype=np.float32)
        except Exception:
            return None

    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any):
        if isinstance(value, np.ndarray):
            vector_bytes = value.astype(np.float32).tobytes()
            await client.setex(key, ttl, vector_bytes.hex())
