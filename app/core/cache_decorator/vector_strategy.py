from io import BytesIO
from typing import Any

import httpx
import numpy as np
from PIL import Image
from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.strategy import Strategy


class VectorStrategy(Strategy):
    async def get(self, client: AsyncRedis, key: str) -> np.ndarray | None:
        data = await client.get(key)
        if data is None:
            return None

        try:
            vector_bytes = bytes.fromhex(data)
            return np.frombuffer(vector_bytes, dtype=np.float32)
        except Exception:
            return None

    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any):
        raw_bytes = await self._to_bytes(value)
        if raw_bytes is not None:
            await client.setex(key, ttl, raw_bytes.hex())

    async def _to_bytes(self, value: Any) -> bytes | None:
        if isinstance(value, np.ndarray):
            return value.astype(np.float32).tobytes()

        if isinstance(value, bytes):
            return value

        if isinstance(value, Image.Image):
            return self._image_to_bytes(value)

        if isinstance(value, str) and value.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(value)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                return self._image_to_bytes(img)

        return None

    def _image_to_bytes(self, img: Image.Image) -> bytes:
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
