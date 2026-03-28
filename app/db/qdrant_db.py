from qdrant_client import QdrantClient

from app.core.settings import settings

# Khởi tạo 1 kết nối duy nhất đến Qdrant Cloud (Connection Pool)
# Nó sẽ duy trì các kết nối mạng liên tục với Qdrant Cloud
qdrant_db = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def get_qdrant_db() -> QdrantClient:
    """
    Trả về client dùng chung chứ không tạo mới để giữ Connection Pool.
    """
    return qdrant_db
