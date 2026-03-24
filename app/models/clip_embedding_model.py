# lib sentence-transformers là một thư viện giúp: text → vector (danh sách số)
# "I love you" -> [0.12, -0.98, 0.44, ..., 0.33]  (384 số), vector này gọi là embedding
# vì máy tính không hiểu chữ, chỉ hiểu số nên text -> vector -> so sánh bằng toán
from io import BytesIO

from PIL import Image
import requests
from sentence_transformers import SentenceTransformer

class ClipEmbeddingModel:
    def __init__(self, device: str):
        self.device = device
        self.model = None

    def load(self):
        print(f'[INFO] Loading CLIP multimodal model on device: {self.device}')
        # Đổi từ 'clip-ViT-B-32' sang bản Multilingual
        # self.model = SentenceTransformer('clip-ViT-B-32-multilingual-v1', device=self.device)
        self.model = SentenceTransformer('clip-ViT-B-32-multilingual-v1', device='cpu')

    def encode_text(self, text: str):
        # CLIP nhận text và trả ra vector 512 chiều
        return self.model.encode([text]).astype('float32')

    def encode_image(self, image_path: str):
        response = requests.get(image_path, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return self.model.encode([img]).astype('float32')
