# Search System - v1.0

Build một AI service (FastAPI) cho semantic text processing, mục tiêu dài hạn là dùng cho search và moderation (dating app).

**Hiện trạng hệ thống:**

1\. Text Embedding
- Dùng sentence-transformers (local model)
- Có TextEmbeddingService với:
  - encode(text)
  - similarity(a, b) dùng cosine

2\. Semantic Similarity API
- Endpoint: POST /api/v1/similarity
- Hoạt động OK, trả về score hợp lý

3\. Vector Search (FAISS)
- Đã tích hợp FAISS (IndexFlatL2)
- Có VectorService:
  - build_index(texts)
  - search(query, top_k)
- Đang dùng biến SAMPLE_DATA trong data/sample_data.py để test
- Search hoạt động đúng (distance nhỏ hơn = giống hơn)

4\. App Structure
- service_registry để quản lý service
- dùng FastAPI lifespan (không dùng on_event)
- vector index đang build trong lifespan (chỉ để demo)

**Vấn đề hiện tại:**
- SAMPLE_DATA nhỏ, nhưng thực tế data sẽ rất lớn (DB)
- Không thể build index tại startup
- Cần chuyển sang kiến trúc production-ready
- Việc load All data từ DB trong lifespan sẽ gặp:
    - 1 vector ~ 384 dims * 4 bytes ~ 1.5 KB, 1M records -> 1.5GB Ram -> startup chậm, timeout deploy
    - Data search không realtime, user tạo data mới -> search không thấy

**Mục tiêu tiếp theo:**

1\. Tách offline indexing:
- script build_index.py
- load data từ DB
- encode → build FAISS index
- save index + metadata

2\. App chỉ load index:
- faiss.read_index(...)
- load metadata

3\. (Optional sau đó)
- incremental update
- persist index
- chuyển sang cosine similarity (IndexFlatIP + normalize)
- vector database

**Flow tham khảo**
```
            +------------------+
            |   Database       |
            +------------------+
                     |
                     v
        +------------------------+
        | Offline Index Builder  |
        +------------------------+
                     |
         index.faiss + metadata
                     |
                     v
        +------------------------+
        |   FastAPI Service      |
        |   (load index only)    |
        +------------------------+
                     |
                     v
                Search API
```

