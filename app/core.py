import torch
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.models.text_model import TextEmbeddingModel
from services.text_embedding_service import TextEmbeddingService

class Settings(BaseSettings):
    PROJECT_NAME: str =  "Nova AI"
    VERSION: str = "1.0.0"
    # Tự động chọn thiết bị: ưu tiên MPS (Mac), sau đó đến CUDA (Nvidia), cuối cùng là CPU
    DEVICE: str = "mps" if torch.backends.mps.is_available() else \
                  "cuda" if torch.cuda.is_available() else "cpu"
    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")

settings = Settings()

class ModelRegistry:
    def __init__(self):
        self.text_model: TextEmbeddingModel | None = None

    def load_models(self):
        print(f"[INFO] Loading text model on device: {settings.DEVICE}")

        self.text_model = TextEmbeddingModel(settings.DEVICE)
        self.text_model.load()

        print('[INFO] Models loaded')

# ModelRegistry → quản lý model
model_registry = ModelRegistry()

class ServiceRegistry:
    def __init__(self):
        self.text_service = None

    def init_services(self, model_registry):
        self.text_service = TextEmbeddingService(model_registry.text_model.model)

# ServiceRegistry → quản lý service
service_registry = ServiceRegistry()