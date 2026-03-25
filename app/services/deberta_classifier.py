"""
DeBERTa-based classifier for scam intent detection.
Uses fine-tuned or pre-trained transformer model for context understanding.
"""

from transformers import pipeline

from app.core.settings import settings


class DeBERTaClassifier:
    """
    DeBERTa-based zero-shot classifier for scam intent detection.
    Can be fine-tuned on labeled data or used as pre-trained model.
    """

    def __init__(self, model_name: str = "microsoft/deberta-large-mnli", mode: str = "zero-shot"):
        """
        Initialize DeBERTa classifier.

        Args:
            model_name: HuggingFace model for classification
            mode: "zero-shot" for zero-shot setup, "fine-tuned" for fine-tuned model
        """
        self.model_name = model_name
        self.mode = mode
        self.device_id = 0 if settings.DEVICE != "cpu" else -1
        self.classifier: object | None = None

        self._load_model()

    def _load_model(self):
        """Load the classifier model."""
        try:
            if self.mode == "zero-shot":
                # Zero-shot classification with DeBERTa
                self.classifier = pipeline("zero-shot-classification", model=self.model_name, device=self.device_id)
            else:
                # For fine-tuned model, regular sequence classification
                self.classifier = pipeline("text-classification", model=self.model_name, device=self.device_id)

            print(f"[INFO] Loaded {self.mode} DeBERTa classifier: {self.model_name}")
        except Exception as e:
            print(f"[ERROR] Failed to load DeBERTa classifier: {e}")
            self.classifier = None

    def predict_zero_shot(self, text: str, candidate_labels: list[str], multi_class: bool = False) -> dict:
        """
        Zero-shot classification - classify text against candidate labels.

        Args:
            text: Input text to classify
            candidate_labels: List of possible labels
            multi_class: Whether to allow multiple labels

        Returns:
            {
                "label": str,  # Top predicted label
                "score": float,  # Confidence score (0-1)
                "all_scores": dict  # All label scores
            }
        """
        if self.classifier is None:
            return {"label": "unknown", "score": 0.0, "all_scores": {}}

        try:
            result = self.classifier(text, candidate_labels, multi_class=multi_class)

            all_scores = dict(zip(result.get("labels", []), result.get("scores", []), strict=False))
            top_label = result.get("labels", ["unknown"])[0]
            top_score = result.get("scores", [0.0])[0]

            return {
                "label": top_label,
                "score": float(top_score),
                "all_scores": all_scores,
            }
        except Exception as e:
            print(f"[ERROR] Zero-shot classification failed: {e}")
            return {"label": "unknown", "score": 0.0, "all_scores": {}}

    def predict_fine_tuned(self, text: str) -> dict:
        """
        Fine-tuned classification - binary scam/legitimate classification.

        Args:
            text: Input text to classify

        Returns:
            {
                "label": str,  # "SCAM" or "LEGITIMATE"
                "score": float  # Confidence score (0-1)
            }
        """
        if self.classifier is None:
            return {"label": "UNKNOWN", "score": 0.0}

        try:
            result = self.classifier(text)
            label = result[0]["label"]
            score = result[0]["score"]
            return {"label": label, "score": float(score)}
        except Exception as e:
            print(f"[ERROR] Fine-tuned classification failed: {e}")
            return {"label": "UNKNOWN", "score": 0.0}

    def predict_scam_intent(self, text: str) -> dict:
        """
        Detect scam intent using zero-shot classification.
        Designed specifically for detecting contact app promotion intent.

        Args:
            text: Input message text

        Returns:
            {
                "is_scam_intent": bool,
                "confidence": float,
                "intent_label": str,
                "all_intents": dict
            }
        """
        if self.classifier is None:
            return {
                "is_scam_intent": False,
                "confidence": 0.0,
                "intent_label": "unknown",
                "all_intents": {},
            }

        # Candidate intents for scam detection
        scam_intent_labels = [
            "trying to persuade someone to move to external contact app",
            "attempting to get contact information",
            "warning against external apps",
            "general discussion about apps",
        ]

        try:
            result = self.predict_zero_shot(text, scam_intent_labels, multi_class=False)

            # Labels that indicate scam intent
            scam_indicators = [
                "trying to persuade someone to move to external contact app",
                "attempting to get contact information",
            ]

            is_scam = result["label"] in scam_indicators
            confidence = result["score"]

            return {
                "is_scam_intent": is_scam,
                "confidence": float(confidence),
                "intent_label": result["label"],
                "all_intents": result["all_scores"],
            }
        except Exception as e:
            print(f"[ERROR] Scam intent prediction failed: {e}")
            return {
                "is_scam_intent": False,
                "confidence": 0.0,
                "intent_label": "unknown",
                "all_intents": {},
            }

    def predict_negation_context(self, text: str) -> dict:
        """
        Detect if text contains negation (warning, avoiding, etc.).

        Args:
            text: Input message text

        Returns:
            {
                "has_negation": bool,
                "negation_type": str,
                "confidence": float
            }
        """
        negation_labels = ["warning or negative statement about an app", "neutral or positive statement"]

        result = self.predict_zero_shot(text, negation_labels, multi_class=False)

        has_negation = result["label"] == "warning or negative statement about an app"
        confidence = result["score"]

        return {
            "has_negation": has_negation,
            "negation_type": result["label"],
            "confidence": float(confidence),
        }
