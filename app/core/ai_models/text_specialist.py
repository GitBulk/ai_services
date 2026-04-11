import asyncio
import gc

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.ai_models.embedding_provider import EmbeddingProvider


class TextSpecialist(EmbeddingProvider):
    async def load(self):
        print(f"--- [RAM] Loading model: {self.model_id} ---")
        self.client = SentenceTransformer(self.model_id, device=self.device)

    async def encode(self, text: str) -> np.ndarray:
        return await asyncio.to_thread(self.client.encode, text)

    async def _perform_unload(self):
        self.client = None
        gc.collect()
