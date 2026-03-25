"""
DeBERTa-based classifier for scam intent detection.
Uses fine-tuned or pre-trained transformer model for context understanding.
"""

import torch
from transformers import pipeline


class DeBERTaClassifier:
    """
    DeBERTa-based zero-shot classifier for scam intent detection.
    Can be fine-tuned on labeled data or used as pre-trained model.
    """

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-small",
        mode: str = "fine-tuned",  # "fine-tuned" or "zero-shot"
        intent_labels: list[str] | None = None,
        device: str = None,
    ):
        # 1. Handle device safely
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        # 2. Validate device
        try:
            self.device = torch.device(device)
        except:
            self.device = torch.device("cpu")

        self.mode = mode
        self.intent_labels = intent_labels or [
            "persuasion_external_contact",
            "money_request",
            "phishing_link",
            "friendly_message",
        ]

        # 3. Load based on mode
        if mode == "fine-tuned":
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model.to(self.device).eval()
        elif mode == "zero-shot":
            self.classifier = pipeline(
                "zero-shot-classification", model=model_name, device=0 if "cuda" in device else -1
            )

    def predict_intent(self, text: str) -> dict:
        # Unified prediction interface
        if not text:
            return {"scam_intent": False, "intent_label": "unknown", "confidence": 0.0, "negation_detected": False}

        try:
            negation = self._has_negation(text)

            if self.mode == "fine-tuned":
                result = self._predict_fine_tuned(text)
            else:
                result = self._predict_zero_shot(text)

            # Apply negation logic
            if negation and result["scam_intent"]:
                result["scam_intent"] = False
                result["negation_detected"] = True

            return result
        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            return {"scam_intent": False, "intent_label": "unknown", "confidence": 0.0, "negation_detected": False}

    def predict_batch(self, texts: list[str]) -> list[dict]:
        return [self.predict_intent(text) for text in texts]

    def _has_negation(self, text: str) -> bool:
        import re

        patterns = [r"\b(no|not|don't|never|can't|without|avoid)\b"]
        return any(re.search(p, text.lower()) for p in patterns)
