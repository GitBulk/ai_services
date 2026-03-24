import torch
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str =  'Nova AI'
    VERSION: str = '1.0.0'
    # Tự động chọn thiết bị: ưu tiên MPS (Mac), sau đó đến CUDA (Nvidia), cuối cùng là CPU
    DEVICE: str = 'mps' if torch.backends.mps.is_available() else \
                  'cuda' if torch.cuda.is_available() else 'cpu'

    VECTOR_BACKEND: str = 'faiss' # or 'memory'
    FAISS_INDEX_PATH: str = 'data/current.index'
    FAISS_METADATA_PATH: str = 'data/current.parquet'
    PRODUCT_FAISS_INDEX_PATH: str = 'data/products_current.index'
    PRODUCT_FAISS_METADATA_PATH: str = 'data/products_current.parquet'
    RERANKER: str = 'cross'
    model_config = SettingsConfigDict(env_file = '.env', extra = 'ignore')

settings = Settings()
