from app.core.config import settings
from app.models.clip_embedding_model import ClipEmbeddingModel
from app.models.text_embedding_model import TextEmbeddingModel


class ModelRegistry:
    def __init__(self):
        self.models = {}
        self._current_model = None

    def load_models(self):
        print(f"[INFO] Loading text model on device: {settings.DEVICE}")
        text_model = TextEmbeddingModel(settings.DEVICE)
        text_model.load()
        self.models["text_embedding"] = text_model

        clip_model = ClipEmbeddingModel(settings.DEVICE)
        clip_model.load()
        self.models["clip_embedding"] = clip_model
        print("[INFO] Models loaded")

    def use_model(self, name: str):
        if name not in self.models:
            raise ValueError(f"Model '{name}' chưa được đăng ký trong ModelRegistry")

        self._current_model = self.get(name)
        return self._current_model

    def encode_text(self, text: str):
        if self._current_model is None or self._current_model.model is None:
            raise ValueError("Text embedding model chưa được load. Hãy gọi load_models() trước encode_text")

        return self._current_model.encode_text(text)

    def encode_image(self, image_input):
        if self._current_model is None or self._current_model.model is None:
            raise ValueError("CLIP model chưa được load. Hãy gọi load_models() trước encode_image")

        return self._current_model.encode_image(image_input)

    def encode_multimodal(self, text: str = None, image_url: str = None):
        if not text and not image_url:
            raise ValueError("Phải cung cấp text hoặc image_url")

        return self._current_model.encode_multimodal(text=text, image_input=image_url)

    def get(self, name):
        return self.models[name]


# ModelRegistry → quản lý model
model_registry = ModelRegistry()
