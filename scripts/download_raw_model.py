from transformers import AutoModelForSequenceClassification, AutoTokenizer

model_id = "moritzlaurer/mDeBERTa-v3-base-mnli-xnli"
save_path = "./models/mdeberta_raw"

# Tải và lưu cục bộ
model = AutoModelForSequenceClassification.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)

model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"--- Đã lưu bản RAW vào {save_path} ---")
