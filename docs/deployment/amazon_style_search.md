## 🚀 Context: Building Amazon-style Search + Related Products System

Xây dựng một hệ thống search & recommendation kiểu Amazon, với kiến trúc tách biệt:

* Rails (Postgres): lưu dữ liệu sản phẩm
* Python (Nova AI services): xử lý AI (embedding, FAISS, rerank)

---

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

---

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

---

## 🎯 Mục tiêu của `text_for_ai`

**KHÔNG phải để đọc cho người dùng**
→ mà để tối ưu cho embedding model (CLIP / SentenceTransformer)

---

## 🔥 Tại sao cần `text_for_ai`?

### 1. Model không hiểu structure DB

DB có:

* category_id
* article_type
* gender

👉 nhưng embedding model chỉ nhận **text**

→ cần flatten thành semantic tokens

---

### 2. Multilingual search (VI + EN)

User có thể search:

* "áo xanh"
* "blue shirt"

→ nên cần mix:

* tiếng Việt: "áo nam màu navy blue"
* tiếng Anh: "navy blue shirt"

---

### 3. Canonicalization (chuẩn hóa từ khóa)

Raw data:

* "Shirts", "shirts", "SHIRTS"

→ normalize thành:

* "shirt"

→ giúp embedding ổn định hơn

---

### 4. Structured semantic tokens (không phải sentence)

Thay vì:

"Sản phẩm áo nam màu xanh chính hãng..."

→ dùng:

```
name. en_hint. article. sub_category. master_category. gender. brand
```

→ giúp model hiểu rõ từng dimension

---

### 5. Tách biệt UI vs AI

* `name` → phục vụ UI (human-readable)
* `text_for_ai` → phục vụ AI (machine-optimized)

---

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

---

### 2. Nova AI (Python)

* Load model (CLIP ViT-B-32)
* Encode:

  * image → vector
  * text_for_ai → vector (optional)
* Normalize vector
* Build FAISS index

---

### 3. Search Flow (planned)

* User query → text embedding
* FAISS search → top K candidates
* Optional rerank
* Combine với:

  * co-visitation (behavioral)
  * category filter

---

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

---

## ⚠️ Constraints

* Dataset hiện tại: Kaggle fashion
* Scale: có thể tăng lên hàng trăm nghìn products
* Ưu tiên:

  * đơn giản nhưng đúng hướng production
  * dễ iterate

---

## 📌 Current Output Sample

```json
{"id":74447,"text_for_ai":"áo nam màu navy blue. navy blue shirt. shirt. topwear. apparel. men. brand adidas"}
{"id":74448,"text_for_ai":"quần/váy nam màu xanh dương. blue jeans. jeans. bottomwear. apparel. men. brand adidas"}
```

---

👉 Hãy tiếp tục từ đây, build **search + recommendation system hoàn chỉnh kiểu Amazon**.
