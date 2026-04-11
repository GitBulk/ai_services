from abc import ABC, abstractmethod
from typing import Any

from redis.asyncio import Redis as AsyncRedis


class Strategy(ABC):
    @abstractmethod
    async def get(self, client: AsyncRedis, key: str) -> Any:
        pass

    @abstractmethod
    async def set(self, client: AsyncRedis, key: str, value: Any, ttl: int, **kwargs: Any) -> None:
        pass
