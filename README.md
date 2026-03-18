# 🚀 Nova AI Service Hub

**Nova AI Service** là hạt nhân xử lý trí tuệ nhân tạo trong hệ sinh thái Nova. Được thiết kế theo kiến trúc **Modular Hub-and-Spoke**, service này không chỉ thực hiện nhiệm vụ kiểm duyệt (Moderation) mà còn là nền tảng cho hệ thống gợi ý (Ranking Feed) và tìm kiếm thông minh.

---

## 🏗 Architecture & Design Patterns

Service hoạt động như một microservice độc lập, giao tiếp với Ruby on Rails Backend thông qua giao thức HTTP/JSON.

* **Framework:** FastAPI (Python 3+)
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
- Python 3+
- Docker & Docker Compose (Khuyên dùng)
- NVIDIA GPU (Tùy chọn, để tăng tốc xử lý)

**Installation**
1. Cài đặt môi trường:
```
- Tạo môi trường ảo (tên là venv):
python3.12 -m venv env_nova

- Kích hoạt
source env_nova/bin/activate

- Kiểm tra python
python --version

pip install --upgrade pip setuptools wheel
pip install torch torchvision torchaudio
pip install -r requirements.txt

- Kiểm tra GPU
python -c "import torch; print('--- STATUS ---'); print('Python Version:', torch.__version__); print('GPU (MPS) Available:', torch.backends.mps.is_available())"

Output expected:
--- STATUS ---
Python Version: 2.10.0
GPU (MPS) Available: True
```
2. Chạy service
```
make run
OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
**📁 Project structure**
```
.
├── app/
│   ├── __init__.py           # Đánh dấu đây là một Python Package
│   ├── main.py               # "Trái tim" hệ thống (Khởi tạo FastAPI, nạp Router)
│   ├── routes.py             # "Controller" (Định nghĩa các API endpoints như /analyze)
|   └── core/                 # "Initializer" (Quản lý .env, cấu hình DEVICE: mps)
│       └── settings.py
│       └── model_registry.py
│       └── service_registry.py
|   └── models/
│       └── text_model.py
│   └── services/             # "Logic tầng thấp"
│       ├── __init__.py
│       └── processor.py      # Xử lý AI thực thụ (Clean text, move to GPU)
|       └── nsfw_service.py   # ViT-based NSFW detector
|       └── vector_service.py # Image embedding engine
├── data/                     # Nơi chứa các Model AI (.pth, .bin) sau này
├── env_nova/                 # Môi trường ảo (Virtual Environment)
├── .env                      # Lưu biến môi trường (PROJECT_NAME, VERSION)
├── .gitignore                # Chặn đẩy env_nova và .env lên Git
└── requirements.txt          # "Gemfile.lock" (Danh sách thư viện: fastapi, torch, pydantic-settings...)
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