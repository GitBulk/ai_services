# 🛡️ Nova AI: Advanced Scam Detection System (Final Version)

**Status**: 🚀 Reviewing

**Version**: 1.0

**Last Updated**: 2026-03-28

---
## Overview
- Bắt các tin nhắn scam/spam trong chat trên app dating.
- Scammer thường dụ dỗ user chuyển sang Telegram, WhatsApp, Viber, Zalo, Messenger hoặc gửi contact ngoài.
- Scammer gửi hình cho user, trên dating app có thể làm mờ hình trước và yêu cầu receiver bấm xác nhận trước khi xem. User có thể report hình và việc đó diễn ra trên dating app mà không cần Nova AI can thiệp.
- Phải hiểu intent của message, tránh false positive (ví dụ: “tôi không dùng Telegram” không bị đánh dấu).
- Scammer có thể dùng hình và bên trong hình có nội dung dung contact họ qua các app ngoài

## 1. Kiến Trúc Phòng Thủ Đa Tầng (Multi-Layer Defense)

Hệ thống hoạt động theo nguyên lý "Phễu lọc" để tối ưu hóa tài nguyên (CPU/GPU) và tốc độ phản hồi.

### Tầng 0: Chặn Tức Thì (Normalization & MD5)
* **Mục tiêu**: Chặn 90% tool spam rải tin nhắn hàng loạt.
* **Xử lý**:
    1. Chuyển chữ thường, Unidecode (bỏ dấu tiếng Việt/ký tự lạ).
    2. Xóa toàn bộ khoảng trắng và ký tự đặc biệt.
    3. Băm MD5 và kiểm tra trong Redis Blacklist.
* **Action**: **Silent Block** (Người gửi vẫn thấy "Sent", người nhận không bao giờ thấy).

### 🛡️ Tầng 1: Thuật Toán Kỹ Thuật (Regex & Levenshtein)
* **Regex**: Quét các pattern số điện thoại (chữ & số), link Telegram, WhatsApp, Zalo.
* **Fuzzy Matching (Levenshtein)**: Đo khoảng cách chỉnh sửa giữa các từ trong chat và danh sách từ khóa cấm (Ví dụ: `t.e.l.e.g.r.a.m` có distance < 2 so với `telegram`).

### 🧠 Tầng 2: Trí Tuệ Nhân Tạo (Qdrant & DeBERTa)
* **Signal 2 (Semantic Search)**: Sử dụng **Qdrant Vector DB** với model `paraphrase-multilingual-MiniLM-L12-v2`. So sánh ngữ nghĩa với các mẫu scam đã được Admin duyệt. Trả về điểm tương đồng (Similarity Score).
* **Signal 3 (Intent Classification)**: Sử dụng **DeBERTa-v3** để phân tích ý định chèo kéo ra ngoài nền tảng và nhận diện ngữ cảnh phủ định (Negation). Trả về điểm ý định (Intent Score) và trạng thái phủ định (Negation).
* **LOGIC SCORING** điểm số để đưa ra kết quả is_scam: true/false hoặc các mức cảnh báo.

### 🕸️ Tầng 3: Phân tích hành vi (Behavioral & Graph Analysis)
Các signal:
- Số lượng tin nhắn gửi trong X phút/giờ.
- Tỷ lệ hội thoại một chiều (sender gửi >> receiver reply).
- Device fingerprint / IP diversity / account age + velocity.
- Graph: nhiều account → cùng 1 Telegram ID / phone.

---

## 2. LOGIC SCORING

Điểm số cuối cùng là sự kết hợp giữa **Nội dung (Content)** và **Ngữ cảnh (Context/Metadata)**.

temp:
### A. Công thức toán học

Hệ thống tính điểm theo hai bước:

1. **Tính điểm thô (Raw Score)**:
  $$
  \text{Raw} = \sum_{i=1}^{n} S_i \cdot w_i
  $$

2. **Áp dụng các hệ số nhân và chuẩn hóa bằng Sigmoid**:
  $$
  \text{Final\_Score} = 100 \times Sigmoid \left( \frac{\text{Raw} \times \prod_{j} M_j}{100} \right)
  $$

3. Quy tắc đặc biệt: Negation Override
```
Nếu có contact info -> bỏ qua Mneg​
```
**Giải thích**:
- Hàm **Sigmoid** ($\sigma$) giúp giới hạn điểm số tự nhiên trong khoảng **0 – 100**, tránh tình trạng điểm bị đẩy quá cao khi nhân nhiều multipliers.
- Ưu điểm so với `min(100, ...)`: mượt mà hơn, ít bị "cắt cứng", và dễ điều chỉnh độ nhạy.


### B. Thành phần điểm thô (Raw Signals - $S_i$)
| Ký hiệu | Tín hiệu | Trọng số ($w$) | Mô tả |
| :--- | :--- | :--- | :--- |
| $S_1$ | **Keyword Score** | 0.4 | Điểm từ Regex và Levenshtein (0-100). |
| $S_2$ | **Semantic Score** | 0.3 | Độ tương đồng vector từ Qdrant (0-100). |
| $S_3$ | **Intent Score** | 0.3 | Độ tin cậy từ DeBERTa về hành vi dụ dỗ (0-100). |

### C. Các hệ số điều chỉnh (Risk Multipliers - $M_j$)
Hệ số nhân áp dụng dựa trên Metadata của tài khoản và cuộc hội thoại:

| Hệ số | Tên | Giá trị | Điều kiện áp dụng |
| :--- | :--- | :--- | :--- |
| $M_{neg}$ | **Negation** | 0.1 | DeBERTa xác nhận câu phủ định (trừ khi có SĐT/ID App). |
| $M_{cross}$ | **Cross-border** | 1.2 | `sender_country != receiver_country`. |
| $M_{age}$ | **New Account** | 1.5 | Tuổi tài khoản < 24 giờ. |
| $M_{trust}$ | **Trusted User** | 0.8 | Tài khoản đã Verify hoặc lịch sử sạch > 30 ngày. |

## 3. Các Ngưỡng Phán Quyết (Thresholds)

| Điểm số | Trạng thái | Hành động (Action) |
| :--- | :--- | :--- |
| **0 - 40** | **Green** | An toàn. Cho phép gửi tin nhắn. |
| **41 - 75** | **Yellow** | **Nghi vấn**: Gắn cờ cảnh báo người nhận + Đẩy về Admin Review. |
| **> 75** | **Red** | **Silent Block**: Chặn tin nhắn phía Server + Gắn nhãn Spammer. |

Bảng chỉ mang tinh chất minh họa, Admin có thể điều chỉnh, có thể áp dụng cơ chế multi version config configuration

## 4. Ví Dụ Minh Họa Logic

**Kịch bản 1**: Một tài khoản mới tạo (2h) từ Nigeria nhắn cho User tại Mỹ: *"I am not here often, add my tele.gram @abc"*.

1.  **Tính Raw Score**:
    * $S_1$ (Keyword `tele.gram`): 90đ
    * $S_2$ (Semantic - giống mẫu cũ): 85đ
    * $S_3$ (Intent - dụ dỗ): 95đ
    * $\Rightarrow Raw = (90 \times 0.4) + (85 \times 0.3) + (95 \times 0.3) = \mathbf{90.0}$
2.  **Áp dụng Multipliers**:
    * $M_{cross}$ (NG -> US): $\times 1.2$
    * $M_{age}$ (< 24h): $\times 1.5$
    * $\Rightarrow Final = 90.0 \times 1.2 \times 1.5 = \mathbf{162.0}$
3.  **Kết quả**: Hành động: **Silent Block**.
4. Nếu trong message có số điện thoại, vd: "Tôi không dùng Telegram, dùng Zalo này: 0123.." thì nhân thêm $M_{Negation}$
5. Cấu hình mẫu, có thể lưu bằng file yaml, db, redis, ..., có thể áp dụng cơ chế multi version configuration
```yaml
# app/core/scoring_config.yaml
thresholds:
  safe: 40
  review_required: 75
  auto_block: 100

weights:
  keyword_weight: 0.4
  semantic_weight: 0.3
  intent_weight: 0.3

multipliers:
  negation_detected: 0.1
  cross_border: 1.2
  new_account_penalty: 1.5 # Tài khoản mới tạo dưới 24h nhân thêm 1.5 điểm rủi ro
```

6. Có thể bổ sung thêm các Multiplier
- $  M_{image}  $: 1.3 nếu tin nhắn kèm ảnh chứa text contact (OCR).
- $  M_{reply_rate}  $: 1.4 nếu reply rate thấp + broadcast pattern.
- $  M_{grooming}  $: dựa trên thời gian chat dài nhưng đột ngột chuyển app.
...

**Kịch bản 2**:

User gửi message: "Anh không dùng Telegram đâu, em gửi Zalo cho anh nhé?” → negation + intent → score giảm mạnh → Green hoặc Yellow


## 5. Cấu Trúc Dữ Liệu Hội Thoại (Context Flow)

AI hiểu được dòng chảy hội thoại và vai trò của người tham gia (Sender/Receiver).
Input JSON sample
```json
{
  "current_message": "Add me on telegram @abc",
  "history": [
    { "role": "sender", "content": "Hi, nice to meet you" },
    { "role": "receiver", "content": "Hello, how can I help?" },
    { "role": "sender", "content": "I prefer talking on another app, it is faster" }
  ],
  "metadata": {
    "sender_country": "NG",
    "receiver_country": "US",
    "language": "en"
  }
}
```

Output JSON sample
```json
{
  "score": ...,
  "keywords_found": {"telegram": 0.95, "contact_outside": 0.82},
  "intent": "refusal_of_external_contact",
  "confidence": 0.91,
  "explanation": "Model phát hiện intent persuasion chuyển nền tảng chat ngoài + obfuscation (te.legram). Không chứa từ phủ định rõ ràng.",
  "detected_patterns": ["telegram_variant", "urgent_contact"],
  "negation_detected": false,
  "language": "en",
  "sender_account_age_hours": ..., // Độ tuổi của tài khoản người gửi (sender) tính bằng giờ, kể từ lúc tài khoản được tạo đến thời điểm gửi tin nhắn hiện tại.
  "sender_message_count_last_24h": ..., // Tổng số tin nhắn mà sender đã gửi trong vòng 24 giờ gần nhất.
  "has_contact_info_on_media": true/false, // Scammer thường gửi ảnh có text bên trong (ảnh chụp màn hình chứa @Telegram, số điện thoại, QR code, hoặc dòng chữ “Add me on WhatsApp”
  "model_version": "..."
}
```

## 6. Admin Feedback Loop (Qdrant)
- Approve Scam: client.upsert tin nhắn vào Qdrant để tăng điểm $S_2$ cho các lần sau.
- Reject Scam: client.delete điểm vector khỏi Qdrant nếu bị chặn nhầm để giảm sai số.

## 7. Future Implementation
- Image/Text in image analysis: Scammer hay gửi ảnh có text Telegram bên trong → cần OCR + vision model (hoặc CLIP-like). **(top priority)**
- Rate limiting + Account level scoring: Không chỉ per message mà per account/session.
- A/B testing cho thresholds.
- Fine-tuning model.

---
Nova AI Team - Chống Scam là một cuộc chiến không hồi kết.