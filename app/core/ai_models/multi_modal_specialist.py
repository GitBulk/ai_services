import asyncio
import gc
from io import BytesIO
from typing import Any

import httpx
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

from app.core.ai_models.embedding_provider import EmbeddingProvider


class MultiModalSpecialist(EmbeddingProvider):
    async def load(self):
        print(f"--- [RAM] Loading model: {self.model_id} ---")
        self.client = SentenceTransformer(self.model_id, device=self.device)

    async def encode(self, text: str = None, image: Any = None) -> np.ndarray:
        if text:
            return await asyncio.to_thread(self.client.encode, text)
        if image:
            return await self._encode_image_to_vector(image)
        raise ValueError("At least one of text or image must be provided")

    async def _perform_unload(self):
        self.client = None
        gc.collect()

    def _encode_text_to_vector(self, text: str) -> np.ndarray:
        return self.client.encode(text)

    async def _encode_image_to_vector(self, image_input: Any) -> np.ndarray:
        if isinstance(image_input, str):
            if image_input.startswith("http"):
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(image_input)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.copy()
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        return await asyncio.to_thread(self.client.encode, img)
