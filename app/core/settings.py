import torch
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str =  'Nova AI'
    VERSION: str = '1.0.0'
    # Tự động chọn thiết bị: ưu tiên MPS (Mac), sau đó đến CUDA (Nvidia), cuối cùng là CPU
    DEVICE: str = 'mps' if torch.backends.mps.is_available() else \
                  'cuda' if torch.cuda.is_available() else 'cpu'

    VECTOR_BACKEND: str = 'faiss' # or 'memory'
    # FAISS_INDEX_PATH: str = 'data/faiss.index'
    # FAISS_METADATA_PATH: str = 'data/metadata.parquet'
    FAISS_INDEX_PATH: str = 'data/faiss_multilingual.index'
    FAISS_METADATA_PATH: str = 'data/metadata_multilingual.parquet'

    model_config = SettingsConfigDict(env_file = '.env', extra = 'ignore')

settings = Settings()
