from qdrant_client import AsyncQdrantClient, QdrantClient

from app.core.config import settings

# Khởi tạo 1 kết nối duy nhất đến Qdrant Cloud (Connection Pool) và Lazy load
_async_qdrant_db: AsyncQdrantClient | None = None


def get_qdrant_db() -> QdrantClient:
    """
    Trả về client dùng chung chứ không tạo mới để giữ Connection Pool.
    """
    return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def get_async_qdrant_db() -> AsyncQdrantClient:
    """
    Trả về client dùng chung chứ không tạo mới để giữ Connection Pool.
    """
    global _async_qdrant_db
    if _async_qdrant_db is None:
        _async_qdrant_db = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    return _async_qdrant_db


async def close_qdrant_client_async():
    global _async_qdrant_db
    if _async_qdrant_db is not None:
        await _async_qdrant_db.close()
        _async_qdrant_db = None
        print("[INFO] Async Qdrant client closed.")
