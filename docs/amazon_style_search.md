## 🚀 Context: Building Amazon-style Search + Related Products System - v1.0

Xây dựng một hệ thống search & recommendation kiểu Amazon, với kiến trúc tách biệt:

* Rails (Postgres): lưu dữ liệu sản phẩm
* Python (Nova AI services): xử lý AI (embedding, FAISS, rerank)
* Dùng file .index và .parquet

## 📦 Data Source

Dữ liệu gốc đến từ Kaggle dataset: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small

* id, gender, masterCategory, subCategory, articleType, baseColour, usage, productDisplayName

Đã:

1. Import CSV → Rails DB (`nova_products`)
2. Normalize dữ liệu (dịch sang tiếng Việt, giữ taxonomy)
3. Lưu các field quan trọng:

* name (UI-friendly, tiếng Việt)
* master_category
* sub_category
* article_type
* base_colour
* gender
* usage
* brand_id
* image_path

## 🧠 Key Design: `text_for_ai`

Tạo thêm field **`text_for_ai`** khi export JSONL sang AI service.

### Ví dụ:

```json
{
  "id": 74447,
  "image_path": "...",
  "text_for_ai": "áo nam màu navy blue. navy blue shirt. shirt. topwear. apparel. men. brand adidas"
}
```

## 🎯 Mục tiêu của `text_for_ai`

**KHÔNG phải để đọc cho người dùng**
→ mà để tối ưu cho embedding model (CLIP / SentenceTransformer)

## 🔥 Tại sao cần `text_for_ai`?

### 1. Model không hiểu structure DB

DB có:

* category_id
* article_type
* gender

👉 nhưng embedding model chỉ nhận **text**

→ cần flatten thành semantic tokens

### 2. Multilingual search (VI + EN)

User có thể search:

* "áo xanh"
* "blue shirt"

→ nên cần mix:

* tiếng Việt: "áo nam màu navy blue"
* tiếng Anh: "navy blue shirt"

### 3. Canonicalization (chuẩn hóa từ khóa)

Raw data:

* "Shirts", "shirts", "SHIRTS"

→ normalize thành:

* "shirt"

→ giúp embedding ổn định hơn

### 4. Structured semantic tokens (không phải sentence)

Thay vì:

"Sản phẩm áo nam màu xanh chính hãng..."

→ dùng:

```
name. en_hint. article. sub_category. master_category. gender. brand
```

→ giúp model hiểu rõ từng dimension

### 5. Tách biệt UI vs AI

* `name` → phục vụ UI (human-readable)
* `text_for_ai` → phục vụ AI (machine-optimized)

## ⚙️ Current Pipeline

### 1. Rails

* Import CSV → DB
* Normalize fields
* Export JSONL:

```json
{
  "id": ...,
  "image_path": "...",
  "text_for_ai": "..."
}
```

### 2. Nova AI (Python)

* Load model (CLIP ViT-B-32)
* Encode:

  * image → vector
  * text_for_ai → vector (optional)
* Normalize vector
* Build FAISS index

### 3. Search Flow (planned)

* User query → text embedding
* FAISS search → top K candidates
* Optional rerank
* Combine với:

  * co-visitation (behavioral)
  * category filter

## 🎯 Goal của conversation tiếp theo

Hệ thống nên có:

1. Thiết kế **search API hoàn chỉnh**

   * query → embedding → FAISS → results

2. Combine:

   * semantic search (vector)
   * co-visitation (behavior)

3. Gợi ý:

   * ranking strategy (Amazon-style)
   * weight tuning (text vs image vs co-visitation)

4. Đưa ra architecture rõ ràng:

   * Rails ↔ Python service
   * caching
   * versioning index


## ⚠️ Constraints

* Dataset hiện tại: Kaggle fashion
* Scale: có thể tăng lên hàng trăm nghìn products
* Ưu tiên:

  * đơn giản nhưng đúng hướng production
  * dễ iterate


## 📌 Current Output Sample

```json
{"id":74447,"text_for_ai":"áo nam màu navy blue. navy blue shirt. shirt. topwear. apparel. men. brand adidas"}
{"id":74448,"text_for_ai":"quần/váy nam màu xanh dương. blue jeans. jeans. bottomwear. apparel. men. brand adidas"}
```

## 2 Cách Triển Khai Search Multimodal Với Text + Image
### Cách 1: 2 FAISS indexes riêng (text + image)
**Implementation**
1. Build 2 FAISS index riêng:
    - faiss_text.index → text embeddings (text_for_ai)
    - faiss_image.index → image embeddings
2. Encode query:
    - query_text → encode text
    - query_image → encode image
3. Search top-K candidates trong cả 2 index:
    - top_text = faiss_text.search(query_text_vec, top_K)
    - top_image = faiss_image.search(query_image_vec, top_K)
4. Compute final_score:
```
final_score = alpha * text_sim + beta * image_sim
```
5. Sort và trả top-K final results

**Ưu điểm**
- Scale tốt: mỗi index nhỏ hơn, dễ update riêng lẻ
- Dynamic weight α/β dễ tune theo query type
- Sau này thêm co_visit_score hoặc weight khác → không cần rebuild index

**Nhược điểm**
- Search phải query 2 index → chậm hơn 1 index duy nhất
- Tốn CPU/RAM hơn do top-K candidates từ 2 index phải merge + rerank
- Cấu hình phức tạp hơn (2 index + normalize vectors)

**Phù hợp khi**
- Dataset lớn (500k → 1M products)
- Muốn dynamic weight α/β theo query
- Muốn thêm co-visitation module sau này

**Flow**
```
Client → query_text / image_url
            │
            ▼
     Encode query → text_service / image_vector
            │
     ┌──────┴──────┐
     ▼             ▼
FAISS_text       FAISS_image
(search top-K)  (search top-K)
     │             │
     └──────┬──────┘
            ▼
   Merge top-K candidates
            │
  Compute final_score = α*text + β*image (+γ*co_visit_score)
            │
          Sort
            │
          Return
```
Features:
- Dynamic α/β/γ
- Scale tốt dataset 500k → 1M
- Can inject co_visitation later
- 2 index → merge + rerank → slightly slower than 1 index

### Cách 2: Concat vector (text + image) vào 1 FAISS index duy nhất
**Implementation**
1. Encode product:
```python
combined_vector = np.concatenate([alpha*text_service, beta*image_vector])
faiss.normalize_L2(combined_vector)
```
2. Build 1 FAISS index duy nhất
3. Encode query:
    - Nếu query text only → concat text_service + zeros(image_dim)
    - Nếu query image only → concat zeros(text_dim) + image_vector
    - Nếu cả text + image → concat trực tiếp
4. FAISS search top-K → trả kết quả

**Ưu điểm**
- 1 index duy nhất → search nhanh, code đơn giản
- Không cần merge top-K 2 index
- Dễ triển khai nhanh cho dataset hiện tại (~40k)

**Nhược điểm**
- Dimension tăng gấp đôi → tốn RAM/CPU, FAISS index nặng
- Weight α/β cố định tại thời điểm build index → khó tune cho từng query
- Khi co_visitation sẵn sàng → phải rerank ngoài FAISS

**Phù hợp khi**
- Dataset vừa (~40k → 100k)
- Muốn triển khai nhanh, ít code
- Dynamic weight chưa quan trọng

**Flow**
```
Client → query_text / image_url
            │
 Encode → text_service / image_vector
            │
 Concat: alpha*text + beta*image → query_vector
            │
         FAISS_concat_index
           (search top-K)
            │
          Return top-K
```

Features:
- 1 FAISS index → search nhanh
- Weight α/β fixed at build time
- Dataset nhỏ → OK
- Co-visitation → rerank outside FAISS

Pseudo code:
```python
def encode_query(query_text=None, query_image_path=None):
    vecs = []
    if query_text:
        tvec = model.encode(query_text)
        tvec = alpha * normalize(tvec)
    else:
        tvec = np.zeros(text_dim)
    if query_image_path:
        img = Image.open(query_image_path).convert("RGB")
        ivec = model.encode(img)
        ivec = beta * normalize(ivec)
    else:
        ivec = np.zeros(image_dim)
    return np.concatenate([tvec, ivec])

def search(query_text=None, query_image_path=None, top_K=10):
    q_vec = encode_query(query_text, query_image_path)
    faiss.normalize_L2(q_vec)
    D, I = faiss_index.search(q_vec[None,:], top_K)
    results = [metadata[i] for i in I[0]]
    return results
```

### So sánh tóm tắt
| Aspect         | 2 Indexes                   | Concat 1 Index                          |
| -------------- | --------------------------- | --------------------------------------- |
| Search speed   | Chậm hơn (2 search + merge) | Nhanh hơn (1 search)                    |
| Memory         | Mỗi index nhỏ hơn           | Dimension tăng gấp đôi                  |
| Weight tuning  | Flexible (α/β dynamic)      | Fixed at build time                     |
| Scale          | Tốt cho 500k → 1M           | OK ~100k, 500k → cần optimize           |
| Co-visitation  | Dễ inject                   | Dễ inject nhưng phải rerank ngoài FAISS |
| Implementation | Phức tạp hơn                | Đơn giản, nhanh                         |

### Khi dataset tăng lên 500k → 1M products
- Cách 1 (2 index):
  - Scale tốt hơn: mỗi index ~250k → FAISS vẫn OK
  - Có thể shard index (split theo category)
  - Co-visitation dễ merge
- Cách 2 (concat 1 index):
  - Dimension double → RAM & disk tăng gấp đôi
  - Cần FAISS IndexIVFFlat hoặc IndexHNSW để scale
  - Nếu top-K search nhỏ (10~50) vẫn chấp nhận được

### Next module: co-visitation
- Cơ chế: behavioral signal, có thể inject vào final_score:
```
final_score = alpha * text_sim + beta * image_sim + gamma * co_visit_score
```
- Cách 1: merge sau top-K search, flexible, weight γ dễ tune
- Cách 2: phải rerank ngoài FAISS, vì FAISS index concat chỉ chứa text+image

### FAISS Index Type: Flat vs IVFFlat vs HNSW

Code hiện tại:
```python
index = faiss.IndexFlatIP(dim)
index.add(vectors_matrix)
```
**IndexFlatIP**
- Cách hoạt động: linear search tất cả vectors trong index.
- Ưu điểm:
    - Simple, dễ triển khai
    - Exact search → trả kết quả chính xác
- Nhược điểm:
    - Chậm khi dataset lớn (>100k vectors)
    - Tốn O(N) mỗi query → không scale cho 1M vectors
- Khi nào dùng: dataset nhỏ (hiện tại 40k), prototyping

**IndexIVFFlat**
- IVF = Inverted File Index
- Cách hoạt động:
    1. Cluster vectors thành nlist centroids (ví dụ 1k)
    2. Mỗi vector được map vào cluster centroid gần nhất
    3. Search: query tìm cluster top-N gần nhất → search vectors trong cluster → nhanh hơn nhiều
- Ưu điểm:
  - Sub-linear search → scale tới 1M+ vectors
  - Memory footprint nhỏ hơn IndexFlat
- Nhược điểm:
  - Approximate search → không hoàn toàn exact
  - Cần train cluster (index.train(vectors_matrix)) trước khi add
- Khi nào dùng: dataset > 100k → 1M+ vectors

**IndexHNSW**
- HNSW = Hierarchical Navigable Small World
- Graph-based approximate nearest neighbor
- Ưu điểm:
  - Tìm nearest neighbor nhanh, sub-linear
  - Thích hợp dataset rất lớn (>1M)
- Nhược điểm:
  - Index xây dựng lâu hơn, memory cao hơn IndexIVFFlat
  - Approximate → có thể miss 1 vài kết quả
- Khi nào dùng: dataset > vài triệu vectors, latency query cực thấp

**So sánh Index**
| Index Type   | Scale      | Exact/Approx | Notes                                    |
| ------------ | ---------- | ------------ | ---------------------------------------- |
| IndexFlatIP  | ~<100k     | Exact        | Good cho prototyping, small dataset      |
| IndexIVFFlat | 100k → 1M+ | Approx       | Train centroids, sub-linear search       |
| IndexHNSW    | 1M+        | Approx       | Graph-based, fast for very large dataset |
