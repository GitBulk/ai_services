# 🚀 Nova AI Service Hub

**Nova AI Service** là hạt nhân xử lý trí tuệ nhân tạo trong hệ sinh thái Nova. Được thiết kế theo kiến trúc **Modular Hub-and-Spoke**, service này không chỉ thực hiện nhiệm vụ kiểm duyệt (Moderation) mà còn là nền tảng cho hệ thống gợi ý (Ranking Feed) và tìm kiếm thông minh.

---

## 🏗 Architecture & Design Patterns

Service hoạt động như một microservice độc lập, giao tiếp với Ruby on Rails Backend thông qua giao thức HTTP/JSON.

* **Framework:** FastAPI (Python 3.9+)
* **AI Engine:** Transformers (HuggingFace), PyTorch.
* **Pattern:** **Strategy Pattern** (Dễ dàng tích hợp thêm các "Spoke" như OCR, Face Detection mà không ảnh hưởng đến core).
* **Database:** Hỗ trợ kết nối Vector Database (Qdrant/pgvector) để lưu trữ embedding độc lập.

---

## 🛠 Các tính năng chính

### 1. Content Moderation (NSFW Detection)
Sử dụng model **Falcon-NSFW** (kiến trúc Vision Transformer) để phân tích nội dung nhạy cảm.
* **Nhãn phân loại:** `Normal`, `Soft`, `Porn`, `Hentai`, `Sexy`.
* **Cơ chế:** Trả về xác suất và hành động gợi ý (`allow`, `flag`, `ban`).

### 2. Feature Extraction (Image Embedding)
Sử dụng **SigLIP** (Google) hoặc **DinoV2** (Meta) để chuyển đổi hình ảnh thành không gian vector.
* **Ứng dụng:** Làm đầu vào cho thuật

Chuyển đổi hình ảnh thành Vector không gian 512/768 chiều.
- Phục vụ thuật toán gợi ý (Recommendation System).
- Hỗ trợ tìm kiếm hình ảnh tương đồng về mặt ngữ nghĩa (Semantic Similarity).

## 🚀 Getting Started
**Prerequisites**
- Python 3.9+
- Docker & Docker Compose (Khuyên dùng)
- NVIDIA GPU (Tùy chọn, để tăng tốc xử lý)

**Installation**
1. Cài đặt môi trường:
```
pip install -r requirements.txt
```
2. Chạy service
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
**📁 Project structure**
```
.
├── main.py              # Entry point của FastAPI
├── services/            # Chức năng AI (Strategy Pattern)
│   ├── base.py          # Abstract Base Class
│   ├── nsfw_service.py  # ViT-based NSFW detector
│   └── vector_service.py# Image embedding engine
├── models/              # Quản lý tải và lưu model
├── Dockerfile           # Docker configuration
└── requirements.txt     # Python dependencies
```
**🛡 Security & Safety**
- Rate Limiting: Ngăn chặn việc spam request làm treo Model AI.
- Circuit Breaker: Ngưỡng chặn tự động 500 bản sao (d=0) trước khi yêu cầu can thiệp thủ công.
- Isolated DB: Dữ liệu AI được lưu trữ riêng biệt để đảm bảo tính riêng tư và hiệu năng.

**🤝 Contribution**
1. Fork dự án.
2. Tạo Feature branch (git checkout -b feature/AmazingAI).
3. Commit thay đổi (git commit -m 'Add some AmazingAI').
4. Push lên branch (git push origin feature/AmazingAI).
5. Mở một Pull Request.