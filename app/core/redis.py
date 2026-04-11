import redis

# import redis.asyncio as async_redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings

_async_redis_client: AsyncRedis | None = None


def get_redis_client():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)


def get_async_redis_client() -> AsyncRedis:
    global _async_redis_client
    if _async_redis_client is None:
        _async_redis_client = AsyncRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,  # False vì chúng ta lưu vector (bytes)
            # === Hai tham số quan trọng ===
            socket_connect_timeout=5,  # Chờ kết nối tối đa 5 giây
            socket_timeout=5,  # Chờ phản hồi lệnh tối đa 5 giây
            # Các tham số tốt khác nên thêm:
            socket_keepalive=True,
            health_check_interval=30,  # Tự động kiểm tra kết nối
            max_connections=100,  # Connection pool size
        )

    return _async_redis_client


async def close_redis_async():
    global _async_redis_client
    if _async_redis_client is not None:
        await _async_redis_client.aclose()
        _async_redis_client = None
