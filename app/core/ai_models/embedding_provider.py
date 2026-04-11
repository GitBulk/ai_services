from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class EmbeddingProvider(ABC):
    def __init__(self, model_id: str, device: str):
        self.model_id = model_id
        self.device = device
        self.client: Any = None

    @abstractmethod
    async def load(self):
        """Logic load model vào RAM/GPU"""
        pass

    @abstractmethod
    async def encode(self, **kwargs) -> np.ndarray:
        """Logic inference thực tế"""
        pass

    async def unload(self):
        """Giải phóng tài nguyên hệ thống"""
        if self.client is not None:
            print(f"--- [RAM] Unloading model: {self.model_id} ---")
            await self._perform_unload()

            self.client = None
        else:
            print(f"--- [INFO] Model {self.model_id} was already empty. ---")

    @abstractmethod
    async def _perform_unload(self):
        """Các lớp con có thể override để giải phóng GPU/VRAM cụ thể"""
        pass
