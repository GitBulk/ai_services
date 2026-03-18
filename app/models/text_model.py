# lib sentence-transformers là một thư viện giúp: text → vector (danh sách số)
# "I love you" -> [0.12, -0.98, 0.44, ..., 0.33]  (384 số), vector này gọi là embedding
# vì máy tính không hiểu chữ, chỉ hiểu số nên text -> vector -> so sánh bằng toán
from sentence_transformers import SentenceTransformer

class TextEmbeddingModel:
    def __init__(self, device: str):
        self.device = device
        self.model = None

    def load(self):
        # model all-MiniLM-L6-v2 hoạt động tốt trên tiếng Anh
        # self.model = SentenceTransformer('all-MiniLM-L6-v2', device = self.device)

        # để support multi language, ta dùng model paraphrase-multilingual-MiniLM-L12-v2
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=self.device)

    def encode(self, text: str):
        # hàm encode sẽ tokenize câu, chạy qua neural network, output vector 384 chiều
        # câu giống nghĩa -> vector gần nhau, câu khác nghĩa -> vector xa nhau.
        # cách cũ, so sánh chuỗi "cheap phone" ≠ "budget smartphone"
        # còn giờ, với vector thì vector("cheap phone") ≈ vector("budget smartphone")
        return self.model.encode(text)
