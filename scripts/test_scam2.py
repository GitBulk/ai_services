from transformers import pipeline

# --- MÔ HÌNH AI ---
classifier = pipeline("zero-shot-classification", model="moritzlaurer/mDeBERTa-v3-base-mnli-xnli")


def final_scam_checker(json_data, ai_score, ai_label):
    meta = json_data["metadata"]

    # TRƯỜNG HỢP 1: XỬ LÝ "CỨNG" BẰNG METADATA (Vượt mặt AI)
    if meta["messages_sent_24h"] > 500:
        return "🚩 BLOCK: SPAM BOT DETECTED (High Volume)", 1.0

    if meta["account_age_days"] < 1 and meta["messages_sent_24h"] > 50:
        return "🚩 BLOCK: NEW ACCOUNT SPAM", 0.98

    # TRƯỜNG HỢP 2: KẾT HỢP AI VÀ METADATA (Suy luận hỗn hợp)
    is_scam_intent = "scammer" in ai_label.lower() or "luring" in ai_label.lower()

    # Nếu AI nghi ngờ > 40% VÀ nick quá mới -> Chặn luôn cho an toàn
    if is_scam_intent and ai_score > 0.4 and meta["account_age_days"] < 2:
        return f"🚩 BLOCK: SUSPICIOUS NEW USER ({ai_score:.2%})", ai_score

    # TRƯỜNG HỢP 3: AI PHÁT HIỆN PHISHING CỰC MẠNH (Dù metadata có đẹp)
    if is_scam_intent and ai_score > 0.9:
        return f"🚩 BLOCK: AI PHISHING DETECTED ({ai_score:.2%})", ai_score

    # TRƯỜNG HỢP 4: AN TOÀN
    return "✅ PASS: CLEAN MESSAGE", ai_score


def transform_strict_context(json_data):
    meta = json_data["metadata"]

    # 1. PHẦN CHỈ THỊ (Ép AI coi Metrics là tối thượng)
    instruction = (
        "TASK: SCAM AUDIT. YOU MUST COMPARE 'METRICS' VS 'CONTENT'.\n"
        "RULE 1: If 'MESSAGES_24H' > 100, label as 'SCAMMER' regardless of how friendly the text is.\n"
        "RULE 2: If 'ACCOUNT_AGE' < 2 days AND 'MESSAGES_24H' > 50, it is a BOT SCAM.\n"
        "RULE 3: Only consider 'SAFE' if BOTH metrics are low (Age > 10, Msgs < 20).\n"
    )

    # 2. PHẦN DỮ LIỆU CỨNG (Đưa lên đầu để AI đọc trước)
    evidence = (
        f"--- HARD EVIDENCE ---\n"
        f"SENDER_AGE: {meta['account_age_days']} DAYS\n"
        f"SENDER_ACTIVITY: {meta['messages_sent_24h']} MESSAGES/24H\n"
        f"LOCATION_MATCH: {meta['sender_country']} to {meta['receiver_country']}\n"
    )

    # 3. PHẦN NỘI DUNG (Để ở cuối)
    content = (
        f"--- MESSAGE CONTENT ---\n"
        f"History: {json_data['history'][0]['content']}\n"
        f"Latest: {json_data['current_message']}\n"
    )

    return f"{instruction}\n{evidence}\n{content}\nVERDICT BASED ON EVIDENCE:"


# --- LUỒNG CHẠY CHÍNH ---
def process_message(raw_json):
    # 1. AI suy luận ngữ nghĩa
    prompt = transform_strict_context(raw_json)  # Hàm bạn đã viết
    print(f"prompt: {prompt}")
    res = classifier(prompt, ["scammer luring user", "legitimate chat"])

    ai_label = res["labels"][0]
    ai_score = res["scores"][0]

    # 2. Gọi Thẩm phán cuối cùng
    verdict, final_score = final_scam_checker(raw_json, ai_score, ai_label)

    return verdict, final_score


raw_json = {
    "current_message": "Bonjour comment vastu",
    "history": [{"role": "sender", "content": "Cher utilisateur, nous avons détecté une activité inhabituelle."}],
    "metadata": {
        "sender_country": "FR",
        "receiver_country": "FR",
        "language": "fr",
        "account_age_days": 1,
        "messages_sent_24h": 900,
    },
}

# TEST THỬ
verdict, score = process_message(raw_json)
print(f"KẾT LUẬN CUỐI CÙNG: {verdict}")
