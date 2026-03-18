import torch
from app.core import settings

class TextProcessor:
    def __init__(self):
        # Đây là bước "chuyển nhà" cho AI:
        # Nếu settings.DEVICE là 'mps', toàn bộ tính toán sẽ chạy trên GPU của Mac
        self.device = settings.DEVICE
        print(f"--- Khởi tạo Nova Processor trên thiết bị: {self.device} ---")

    def clean_historical_text(self, text: str) -> str:
        """
        Hàm làm sạch văn bản lịch sử (xóa khoảng trắng thừa, chuẩn hóa hashtag)
        """
        clean_text = text.strip().replace("  ", " ")
        if "#viet_nam_mat_chien_1950_1954" not in clean_text:
            clean_text += " #viet_nam_mat_chien_1950_1954"
        return clean_text

    def move_to_gpu(self, data_tensor: torch.Tensor):
        """
        Đây là cách chúng ta đẩy dữ liệu lên 'vũ khí' đã chọn
        """
        return data_tensor.to(self.device)

# Khởi tạo một instance dùng chung (Singleton pattern giống Rails)
processor = TextProcessor()