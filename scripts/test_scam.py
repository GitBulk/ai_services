# import pycountry
import re
import unicodedata

from transformers import pipeline

# --- BƯỚC 1: KHỞI TẠO MÔ HÌNH (Chỉ chạy 1 lần) ---
print("Đang nạp mô hình mDeBERTa (vui lòng đợi)...")
classifier = pipeline("zero-shot-classification", model="moritzlaurer/mDeBERTa-v3-base-mnli-xnli")

# --- BƯỚC 2: CÁC HÀM HỖ TRỢ (Helper Functions) ---
# def get_country_name(code):
#     try:
#         return pycountry.countries.get(alpha_2=code.upper()).name
#     except:
#         return code

country_map = {
    "BD": "Bangladesh",
    "NG": "Nigeria",
    "US": "United States",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "ES": "Spain",
    "BR": "Brazil",
}


def get_country_name(code):
    return country_map.get(code.upper(), code)


# def transform_strict_context(json_data):
#     meta = json_data["metadata"]
#     s_country = get_country_name(meta["sender_country"])
#     r_country = get_country_name(meta["receiver_country"])

#     # Chỉ dẫn nghiêm ngặt để AI không bị "ngọt mật chết ruồi"
#     # instruction = (
#     #     "CRITICAL INSTRUCTION: You are a fraud detection expert. Analyze if this is a 'PLATFORM LURING' attempt. "
#     #     "A geographic mismatch (e.g., Sender in Nigeria chatting in German to a Receiver in Germany) "
#     #     "combined with a new account and high message volume is a 99% scam signal.\n"
#     # )

#     instruction = (
#         "CRITICAL INSTRUCTION: You are a fraud detection expert. Analyze 'PLATFORM LURING' attempts. "
#         "Focus on INCONSISTENCIES: If a Sender's location does not align with their used language, "
#         "or if a new account has abnormally high message volume, it is a high-risk scam signal. "
#         "Evaluate based on the provided METRICS and DIALOGUE flow."
#     )

#     # Chỉ số hành vi thực tế từ hệ thống (Redis + DB)
#     metrics = (
#         f"METRICS:\n"
#         f"- Geopolitics: From {s_country} to {r_country}\n"
#         f"- Account Age: {meta['account_age_days']} day(s)\n"
#         f"- Messages in 24h: {meta['messages_sent_24h']}\n"
#     )

#     # Lịch sử hội thoại để AI thấy sự dẫn dụ (Sequence)
#     chat_history = "DIALOGUE:\n"
#     for msg in json_data["history"]:
#         role = "STRANGER" if msg["role"] == "sender" else "USER"
#         chat_history += f"[{role}]: {msg['content']}\n"

#     current_msg = f"LATEST_MESSAGE_TO_EVALUATE: {normalize_text(json_data['current_message'])}"

#     return f"{instruction}\n{metrics}\n{chat_history}\n{current_msg}"


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


def normalize_text(text):
    # 1. Chuyển Unicode về dạng chuẩn (Ví dụ: Têlêgråm -> Telegram)
    # NFKD sẽ tách các dấu ra khỏi chữ cái, sau đó encode ASCII sẽ loại bỏ các dấu đó
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # 2. Regex: Loại bỏ tất cả ký tự KHÔNG PHẢI là chữ cái (a-z) hoặc số (0-9)
    # Ví dụ: T.e.l.e.g.r.a.m -> Telegram, @Sūppørt -> Support
    # Lưu ý: Ta giữ lại khoảng trắng để không bị dính các từ vào nhau
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # 3. Loại bỏ khoảng trắng thừa (Double spaces)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# --- BƯỚC 3: DỮ LIỆU TEST ---
# raw_json = {
#     "current_message": "Hey Baby, wenn du Zeit hast, füge mich zu deinem Telegram hinzu. Ich denke, dass Chatten per Telegram besser ist",
#     "history": [
#         {"role": "sender", "content": "Hallo, wie geht es dir?"},
#         {"role": "receiver", "content": "I am fine, but who are you?"},
#     ],
#     "metadata": {
#         "sender_country": "NG",
#         "receiver_country": "DE",
#         "language": "de",
#         "account_age_days": 1,
#         "messages_sent_24h": 450,
#     },
# }

# raw_json = {
#     "current_message": "你好，我的爱人，让我们在 Telegran 上谈谈吧，我的名字在那里，达维拉·席尔瓦·戈麦斯 (Davila Silva Gomes)",
#     "history": [],
#     "metadata": {
#         "sender_country": "BR",
#         "receiver_country": "DE",
#         "language": "de",
#         "account_age_days": 1,
#         "messages_sent_24h": 40,
#     },
# }

# T.e.l.e.g.r.a.m Têlêgråm
# raw_json = {
#     # "current_message": "Votre compte a un problème technique, veuillez contacter T.e.l.e.g.r.a.m @Support_Admin pour le résoudre immédiatement.",
#     "current_message": "Bonjour, comment vas-tu?",
#     "history": [{"role": "sender", "content": "Cher utilisateur, nous avons détecté une activité inhabituelle."}],
#     "metadata": {
#         "sender_country": "FR",  # Bangladesh (Giả danh Support hệ thống)
#         "receiver_country": "FR",  # Pháp
#         "language": "fr",
#         "account_age_days": 1,  # Vừa lập nick đã đi "hỗ trợ"
#         "messages_sent_24h": 9,
#     },
# }


raw_json = {
    "current_message": "Bonjour comment vastu",
    "history": [{"role": "sender", "content": "Cher utilisateur, nous avons détecté une activité inhabituelle."}],
    "metadata": {
        "sender_country": "FR",
        "receiver_country": "FR",
        "language": "fr",
        "account_age_days": 1,
        "messages_sent_24h": 10,
    },
}

# --- BƯỚC 4: CHẠY PHÂN TÍCH ---
if __name__ == "__main__":
    print("\n[1] Đang xử lý ngữ cảnh...")
    prompt = transform_strict_context(raw_json)
    print(f"\n[2] prompt: {prompt}")
    print("[3] AI đang suy luận...")
    candidate_labels = ["scammer luring user to another app", "legitimate friendly conversation"]

    result = classifier(prompt, candidate_labels)

    print("\n" + "=" * 40)
    print("KẾT QUẢ KIỂM TRA AN NINH")
    print("=" * 40)
    for label, score in zip(result["labels"], result["scores"]):
        indicator = "🚩 [NGUY HIỂM]" if score > 0.8 else "✅ [AN TOÀN]"
        print(f"{indicator} {label}: {score:.2%}")
    print("=" * 40)
