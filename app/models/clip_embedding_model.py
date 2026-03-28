# lib sentence-transformers là một thư viện giúp: text → vector (danh sách số)
# "I love you" -> [0.12, -0.98, 0.44, ..., 0.33]  (384 số), vector này gọi là embedding
# vì máy tính không hiểu chữ, chỉ hiểu số nên text -> vector -> so sánh bằng toán
from io import BytesIO

import faiss
import numpy as np
import requests
from PIL import Image
from sentence_transformers import SentenceTransformer


class ClipEmbeddingModel:
    def __init__(self, device: str, text_weight=0.7, image_weight=0.3, model_name: str = "clip-ViT-B-32"):
        self.device = device
        self.text_weight = text_weight
        self.image_weight = image_weight
        self.model_name = model_name
        self.model = None

    def load(self):
        print(f"[INFO] Loading CLIP model {self.model_name} on device: {self.device}")
        self.model = SentenceTransformer(self.model_name, device=self.device)

    def encode_text(self, text: str) -> np.ndarray:
        self._ensure_loaded()
        # vector sẽ có kết quả (512,)
        vector = self.model.encode([text]).astype("float32")[0]
        # normalize cần param là (N, dim), vd: (1, 512) nên cần reshape
        faiss.normalize_L2(vector.reshape(1, -1))

        return vector  # (512,)

    def encode_image(self, image_input) -> np.ndarray:
        self._ensure_loaded()

        if isinstance(image_input, str):
            if image_input.startswith("http"):
                response = requests.get(image_input, timeout=5)
                img = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                # Mở thẳng file từ ổ cứng
                img = Image.open(image_input).convert("RGB")
        else:
            img = image_input

        # vector sẽ có kết quả (512,)
        vector = self.model.encode([img]).astype("float32")[0]
        faiss.normalize_L2(vector.reshape(1, -1))

        return vector

    def encode_multimodal(self, text=None, image_input=None):
        """
        Trả về vector concat đã normalize (dim = 1024)
        """
        self._ensure_loaded()

        # text
        if text:
            t_vec = self.encode_text(text)
        else:
            t_vec = np.zeros(512, dtype="float32")

        # image
        if image_input:
            i_vec = self.encode_image(image_input)
        else:
            i_vec = np.zeros(512, dtype="float32")

        # combined có dạng (1024,)
        combined = np.concatenate([self.text_weight * t_vec, self.image_weight * i_vec]).astype("float32")
        faiss.normalize_L2(combined.reshape(1, -1))

        return combined

    def _ensure_loaded(self):
        if self.model is None:
            raise RuntimeError("Model not loaded. Call .load() first.")
