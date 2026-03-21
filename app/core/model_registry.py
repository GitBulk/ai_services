from app.models.text_model import TextEmbeddingModel
from app.core.settings import settings
import numpy as np

class ModelRegistry:
    def __init__(self):
        self.models = {}

    def load_models(self):
        print(f'[INFO] Loading text model on device: {settings.DEVICE}')

        model = TextEmbeddingModel(settings.DEVICE)
        model.load()

        self.models['text_embedding'] = model
        print('[INFO] Models loaded')

    def encode_text(self, text: str):
        text_model = self.get('text_embedding')
        if text_model is None or text_model.model is None:
            raise ValueError('Text embedding model chưa được load. Hãy gọi load_models() trước encode_text')

        return text_model.embed(text)

    def get(self, name):
        return self.models[name]

# ModelRegistry → quản lý model
model_registry = ModelRegistry()

