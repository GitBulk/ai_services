# Tài liệu Thiết kế Hệ thống Related Products (Amazon Style)
**Dự án:** Nova AI Search & Recommendation
**Stack:** Ruby on Rails (Postgres 9.5) + Python (FAISS, CLIP-ViT-B-32)
**Cập nhật:** 29/03/2026
**Version:** 0.1

---

## 1. Kiến trúc Tổng thể (3 Tầng Logic)

Hệ thống được thiết kế để cân bằng giữa **Độ chính xác ngữ nghĩa (AI)**, **Hành vi thực tế (Data)** và **Yêu cầu kinh doanh (Business)**.

### Tầng 1: Semantic Similarity (Độ tương đồng ngữ nghĩa)
* **Công cụ:** CLIP-ViT-B-32 + FAISS (`IndexFlatIP`).
* **Mục tiêu:** Tìm các sản phẩm "trông giống" hoặc "có mô tả tương đồng" (Substitutes).
* **Ứng dụng:** Gợi ý khi khách xem mẫu này nhưng muốn tham khảo mẫu khác tương tự.

### Tầng 2: Behavioral Association (Liên kết hành vi)
* **Công cụ:** Market Basket Analysis (Dữ liệu `orders` & `line_items` trong 3 tháng).
* **Mục tiêu:** Tìm các cặp sản phẩm thường được mua cùng nhau (Complements).
* **Chỉ số:** **Confidence** (Độ tin cậy) và **Lift** (Độ nâng).

### Tầng 3: Business Ranking (Sắp xếp theo nghiệp vụ)
* **Công cụ:** Python Logic trên Nova AI.
* **Mục tiêu:** Lọc bỏ sản phẩm lỗi, điều tiết theo phân khúc giá, và ưu tiên hàng Best-seller.

---

## 2. Luồng dữ liệu (Data Flow)

1.  **Rails (Export):** Xuất file JSONL chứa `id`, `text_for_ai`, `price`, `category_id`, `popularity_score`.
2.  **Rails (Behavior):** Xuất dữ liệu giỏ hàng (Baskets) từ `line_items` (giới hạn 3 tháng gần nhất).
3.  **Nova AI (Build):** Load JSONL vào Memory, build FAISS Index từ `text_for_ai`.
4.  **Nova AI (Compute):** Tính toán ma trận `pair_counts` và `item_counts` để sẵn sàng tính Confidence/Lift.

---

## 3. Logic Xử lý & Pseudo Code (Python)

### A. Tính toán Confidence (Độ tin cậy mua kèm)
Dùng để xác định sức mạnh của mối quan hệ $A \rightarrow B$.

$$Confidence(A \rightarrow B) = \frac{\text{Số đơn chứa cả A và B}}{\text{Tổng số đơn chứa A}}$$

```python
# Tính toán trước (Offline/Batch)
from collections import Counter

item_counts = Counter() # {product_id: count}
pair_counts = Counter() # {(id_a, id_b): count}

def calculate_associations(baskets):
    for basket in baskets:
        unique_items = set(basket)
        for item in unique_items:
            item_counts[item] += 1
        for a, b in combinations(sorted(list(unique_items)), 2):
            pair_counts[(a, b)] += 1
            pair_counts[(b, a)] += 1

def get_associations(p_id, min_conf=0.2):
    count_a = item_counts.get(p_id, 0)
    if count_a == 0: return []
    
    results = []
    for (a, b), common_count in pair_counts.items():
        if a == p_id:
            conf = common_count / count_a
            if conf >= min_conf:
                results.append({'id': b, 'conf': conf})
    return sorted(results, key=lambda x: x['conf'], reverse=True)
```