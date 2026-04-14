import asyncio

from app.core.ai_models.embedding_provider import EmbeddingProvider
from app.core.ai_models.models_config import MODEL_DEFINITIONS


class ModelManager:
    def __init__(self):
        # Lưu trữ _blueprints: { "model_name": (ProviderClass, config) }
        self._blueprints: dict[str, tuple[type[EmbeddingProvider], dict]] = {}
        # Lưu trữ instance đã load vào RAM: { "model_name": ProviderInstance }
        self._loaded_instances: dict[str, EmbeddingProvider] = {}
        self._lock = asyncio.Lock()

    def load_definitions(self, definitions: dict = None):
        if definitions is None:
            definitions = MODEL_DEFINITIONS

        for name, params in definitions.items():
            self.register_model(name, params["provider_cls"], **params["config"])

        print(f"[INFO] ModelManager: Loaded {len(definitions)} definitions.")

    def register_model(self, name: str, provider_cls: type[EmbeddingProvider], **config):
        """Chỉ đăng ký thông tin, chưa tốn RAM"""
        self._blueprints[name] = (provider_cls, config)

    async def get_model(self, name: str) -> EmbeddingProvider:
        """Lazy load model khi cần dùng"""
        if name in self._loaded_instances:
            return self._loaded_instances[name]

        if name not in self._blueprints:
            raise ValueError(f"Model {name} not registered")

        async with self._lock:
            # Check lại lần nữa sau khi có lock (Double-checked locking)
            if name in self._loaded_instances:
                return self._loaded_instances[name]

            cls, config = self._blueprints[name]
            instance = cls(**config)
            # load model vào RAM/GPU
            await instance.load()

            self._loaded_instances[name] = instance
            return instance

    async def warm_up(self):
        """Eagerly load all registered models into RAM concurrently."""
        names = list(self._blueprints.keys())
        await asyncio.gather(*[self.get_model(name) for name in names])
        print(f"[INFO] ModelManager: Warmed up {len(names)} models: {names}")

    async def clear_all(self):
        """Xóa tất cả instance đã load vào RAM"""
        async with self._lock:
            unload_tasks = [instance.unload() for instance in self._loaded_instances.values()]
            if unload_tasks:
                await asyncio.gather(*unload_tasks)

        self._loaded_instances.clear()
        print("[INFO] ModelManager: All instances have been safely unloaded.")
