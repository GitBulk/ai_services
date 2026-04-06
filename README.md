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
│       └── config.py         # Tương đương database.yml + secrets.yml
|   └── db/
│       ├── session.py        # Sử dụng config để tạo engine
|   └── models/
│       └── text_model.py
│   └── services/             # "Logic tầng thấp"
|       └── ranking/
|           └── heuristic_reranker.py
|           └── corss_encoder_reranker.py
|       └── retrieval/
|           └── retriever.py
│       ├── __init__.py
│       └── processor.py      # Xử lý AI thực thụ (Clean text, move to GPU)
|       └── nsfw_service.py   # ViT-based NSFW detector
|       └── vector_service.py # Image embedding engine
├── data/                     # Nơi chứa các Model AI (.pth, .bin), service chỉ đọc data/current.index, data/current.parquet - If it works, don't touch it
|   ├── faiss_20260320_0100.index
|   ├── metadata_20260320_0100.parquet
|   ├── faiss_20260321_0200.index
|   ├── metadata_20260321_0200.parquet
|   ├── current.index     -> symlink
|   └── current.parquet   -> symlink
├── ai_models/                # EFS MOUNT POINT (Dữ liệu nặng, chia theo Model & Version)
|   ├── mdeberta/             # Folder cho model mDeBERTa
|   │   ├── v_20260604_0910/  # Chứa config.json, model.safetensors, v.v.
|   │   ├── v_20260610_1500/
|   │   └── current ----------> (Symlink trỏ đến folder version đang chạy)
|   │
|   └── modelXYZ/             # Folder cho các model AI khác trong tương lai
|        ├── v_20260304_1910/
|        └── current ----------> (Symlink trỏ đến folder version đang chạy)
├── env_nova/                 # Môi trường ảo (Virtual Environment)
├── .env                      # Lưu biến môi trường (PROJECT_NAME, VERSION)
├── .gitignore                # Chặn đẩy env_nova và .env lên Git
└── requirements.txt          # "Gemfile.lock" (Danh sách thư viện: fastapi, torch, pydantic-settings...)
```

**Database Migration:**

***1. Relation db (Postgres 9.5)***
```bash
pip install alembic
alembic init alembic
```
Sửa database url trong `alembic/env.py`
```python
# Trong file alembic/env.py
from app.core.settings import settings
from app.db.session import Base
# Import các model của bạn vào đây để Alembic tự động nhận diện (Autogenerate)
from app.models.training import NovaTrainingData 

config = context.config
# Nạp URL từ Settings trơn của bạn
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata # Để dùng tính năng tự tạo migration
```
Tạo file migration
```bash
alembic revision -m "create_recommendation_configs_table"
```
xem file alembic/versions/93f29d2de824_create_recommendation_configs_table.py

Kiểm tra lệnh SQL mà Alembic sẽ chạy
```bash
alembic upgrade head --sql
```

Chạy migration
```bash
alembic upgrade head
```

***2. Qdrant DB***
```bash
pip install -e .
```
Quy trình tạo migration với Qdrant:
- Tạo file migration:
```bash
qdrant migrate -m "tên_thay_đổi"
```
- Viết code: Mở file trong versions/, dùng các helper như self.add_index(...) hoặc self.create_col(...).
- Chạy migration:
```bash
qdrant migrate --up
```

**ruff - linter, formater code**
- Please check rule in pyproject.toml
- Kiểm tra lỗi Linting
```bash
# Quét 2 file cùng lúc
ruff check app/routes.py scripts/build_product_index.py

# Quét riêng thư mục models
ruff format app/models/
```
- Tự động fix lỗi
```bash
ruff check --fix app/routes.py
```

**Config Workspace Settings**

.vscode/settings.json
```json
{
    "python.analysis.extraPaths": ["./"],
    "python.autoComplete.extraPaths": ["./"],

    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        }
    }
}
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