from functools import lru_cache

from app.core.ai_models.model_manager import ModelManager
from app.core.model_registry import ModelRegistry, model_registry


def get_ai_model_registry() -> ModelRegistry:
    # Deprecated
    return model_registry


@lru_cache
def get_model_manager() -> ModelManager:
    return ModelManager()
