import torch
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Nova AI"
    VERSION: str = "1.0.0"
    # --- AI Engine Config ---
    # Tự động chọn thiết bị: ưu tiên MPS (Mac), sau đó đến CUDA (Nvidia), cuối cùng là CPU
    DEVICE: str = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

    VECTOR_BACKEND: str = "qdrant"  # 'memory' | faiss | qdrant
    # --- Qdrant Config ---
    QDRANT_URL: str = "QDRANT_URL"
    QDRANT_API_KEY: str = "QDRANT_API_KEY"
    QDRANT_ENVIRONMENT: str = "dev"  # dev | staging | production
    TEXT_WEIGHT: float = 0.5
    IMAGE_WEIGHT: float = 0.5

    # Giữ lại các path FAISS nếu muốn dùng parallel
    FAISS_INDEX_PATH: str = "data/current.index"
    FAISS_METADATA_PATH: str = "data/current.parquet"
    PRODUCT_FAISS_INDEX_PATH: str = "data/products_current.index"
    PRODUCT_FAISS_METADATA_PATH: str = "data/products_current.parquet"
    RERANKER: str = "cross"

    # --- Database (Gom nhóm) ---
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "nova_db_name"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
