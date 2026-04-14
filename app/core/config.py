import os

import torch
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Nova AI"
    VERSION: str = "1.0.0"
    APP_ENV: str = "production"  # dev | staging | production

    @property
    def is_development(self) -> bool:
        print("--- DEBUG SETTINGS ---")
        return self.APP_ENV == "dev"

    # --- AI Engine Config ---
    # Auto-detected: mps > cuda > cpu. Can be overridden via DEVICE= in .env:
    # Reads from .env if DEVICE=cpu (or any value) is set there
    # Falls back to auto-detection (mps → cuda → cpu) if not set
    DEVICE: str = ""

    @model_validator(mode="after")
    def set_device(self) -> "Settings":
        if not self.DEVICE:
            if torch.backends.mps.is_available():
                self.DEVICE = "mps"
            elif torch.cuda.is_available():
                self.DEVICE = "cuda"
            else:
                self.DEVICE = "cpu"
        return self

    VECTOR_BACKEND: str = "qdrant"  # 'memory' | faiss | qdrant
    # --- Qdrant Config ---
    QDRANT_URL: str = "QDRANT_URL"
    QDRANT_API_KEY: str = "QDRANT_API_KEY"
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

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def database_url(self) -> str:
        return f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Auth ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- OpenAI ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    AI_MODEL_PATH: str = "./models/mdeberta_raw"
    # 1: hoạt đông offline, nếu chưa tải model về từ trước thì văng lỗi
    # 0: ưu tiên dùng bản model đã tải về trước, nếu chưa có sẽ kết nối hugging face để tải.
    TRANSFORMERS_OFFLINE: str = "0"
    HF_DATASETS_OFFLINE: str = "0"


settings = Settings()
# Ép biến môi trường hệ thống ngay sau khi load settings ---
# Điều này đảm bảo thư viện transformers đọc đúng cấu hình Offline
os.environ["TRANSFORMERS_OFFLINE"] = settings.TRANSFORMERS_OFFLINE
os.environ["HF_DATASETS_OFFLINE"] = settings.HF_DATASETS_OFFLINE
