from app.models.text_embedding_model import TextEmbeddingModel
from app.models.clip_embedding_model import ClipEmbeddingModel
from app.core.settings import settings
import numpy as np

class ModelRegistry:
    def __init__(self):
        self.models = {}

    def load_models(self):
        print(f'[INFO] Loading text model on device: {settings.DEVICE}')
        text_model = TextEmbeddingModel(settings.DEVICE)
        text_model.load()
        self.models['text_embedding'] = text_model

        clip_model = ClipEmbeddingModel(settings.DEVICE)
        clip_model.load()
        self.models['clip_embedding'] = clip_model
        print('[INFO] Models loaded')

    def encode_text(self, text: str):
        text_model = self.get('text_embedding')
        if text_model is None or text_model.model is None:
            raise ValueError('Text embedding model chưa được load. Hãy gọi load_models() trước encode_text')

        return text_model.embed(text)

        # Thêm hàm tiện ích gọi CLIP
    def encode_multimodal(self, text: str = None, image_url: str = None):
        clip = self.get('clip_embedding')
        if image_url:
            return clip.encode_image(image_url)

        if text:
            return clip.encode_text(text)

        raise ValueError('Phải cung cấp text hoặc image_url')

    def get(self, name):
        return self.models[name]

# ModelRegistry → quản lý model
model_registry = ModelRegistry()

