import re
import unicodedata
from difflib import SequenceMatcher

from transformers import pipeline

from app.core.settings import settings


class ScamDetectionService:
    """
    Detects scam/spam messages with fuzzy matching and ML-based context analysis.
    Handles multiple languages and contact app variations.
    """

    def __init__(self):
        self.device = settings.DEVICE
        self.classifier = None  # Lazy load on first use
        self._classifier_initialized = False

        # Contact app keywords to detect (base forms)
        self.contact_apps = {
            "telegram": ["telegram", "tg", "tele"],
            "whatsapp": ["whatsapp", "whatapp", "whats app", "wa"],
            "viber": ["viber", "vibe"],
            "zalo": ["zalo", "za lo"],
            "messenger": ["messenger", "messanger", "facebook messenger", "fb messenger"],
        }

        # Multilingual variations
        self.language_variations = {
            "vi": {  # Vietnamese
                "telegram": ["telegram", "tele", "tg"],
                "whatsapp": ["whatsapp", "wa"],
                "viber": ["viber"],
                "zalo": ["zalo"],
                "messenger": ["messenger", "fb"],
            },
            "es": {  # Spanish
                "telegram": ["telegram", "telegrama", "tg"],
                "whatsapp": ["whatsapp", "wasap", "wa"],
                "viber": ["viber"],
                "zalo": ["zalo"],
                "messenger": ["messenger", "mensajero"],
            },
            "en": {  # English
                "telegram": ["telegram", "tg"],
                "whatsapp": ["whatsapp", "wa"],
                "viber": ["viber"],
                "zalo": ["zalo"],
                "messenger": ["messenger"],
            },
        }

        # Load zero-shot classification model for context understanding
        try:
            self.classifier = pipeline(
                "zero-shot-classification", model="facebook/bart-large-mnli", device=0 if self.device != "cpu" else -1
            )
        except Exception as e:
            print(f"[WARNING] Could not load classifier model: {e}")
            self.classifier = None

    def normalize_text(self, text: str) -> str:
        """
        Normalize text by:
        - Converting to lowercase
        - Removing accents
        - Normalizing Unicode homoglyphs (e.g., Cyrillic 'а' to Latin 'a')
        """
        text = text.lower()

        # NFD normalization and accent removal
        text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

        # Replace common Unicode lookalikes
        homoglyph_map = {
            "а": "a",
            "е": "e",
            "о": "o",
            "р": "p",
            "с": "c",
            "у": "y",
            "х": "x",
            "А": "A",
            "Е": "E",
            "О": "O",
            "Р": "P",
            "С": "C",
            "У": "Y",
            "Х": "X",
        }
        for cyrillic, latin in homoglyph_map.items():
            text = text.replace(cyrillic, latin)

        return text

    def remove_separators(self, text: str) -> str:
        """Remove dots, underscores, hyphens between characters: te.le.gram -> telegram"""
        # This pattern removes separators between letters
        text = re.sub(r"([a-z])[\.\-_\s]+([a-z])", r"\1\2", text)
        return text

    def fuzzy_match(self, text: str, keywords: list[str], threshold: float = 0.75) -> tuple[bool, float]:
        """
        Fuzzy match keywords with threshold.
        Returns (is_match, confidence_score)
        """
        text_normalized = self.normalize_text(self.remove_separators(text))

        for keyword in keywords:
            keyword_normalized = self.normalize_text(keyword)

            # Check if keyword is substring
            if keyword_normalized in text_normalized:
                return True, 1.0

            # Fuzzy matching using SequenceMatcher
            matcher = SequenceMatcher(None, keyword_normalized, text_normalized)
            ratio = matcher.ratio()

            if ratio >= threshold:
                return True, ratio

        return False, 0.0

    def detect_keywords(self, text: str, language: str = "en") -> dict:
        """
        Detect contact app keywords in text with fuzzy matching.
        Returns dict with detected apps and confidence scores.
        Uses context windows to avoid false positives.
        """
        detected = {}

        # Get keywords for language
        lang_keywords = self.language_variations.get(language, self.language_variations["en"])

        for app, keywords in lang_keywords.items():
            is_match, confidence = self.fuzzy_match(text, keywords, threshold=0.7)
            if is_match:
                # Additional check: is the keyword in a context that suggests promotion?
                if self._is_promotion_context(text, app, language):
                    detected[app] = confidence

        return detected

    def _is_promotion_context(self, text: str, app: str, language: str) -> bool:
        """
        Check if the keyword appears in a context suggesting promotion.
        Returns True if likely being promoted, False if just mentioned.
        """
        text_lower = text.lower()
        import re

        # Negative patterns - indicates NOT promoting
        negative_patterns = [
            r"\bno\b\s+" + app,  # "no telegram"
            r"don't\s+use\s+" + app,
            r"i\s+don't.*" + app,
            r"dont\s+use\s+" + app,
            r"without\s+" + app,
            r"except\s+" + app,
            r"avoid\s+" + app,
            r"ban.*" + app,
            r"block.*" + app,
            r"beware.*" + app,
            app + r"\s+scam",
            app + r"\s+.*warn",
            app + r"\s+.*danger",
            r"discussion.*" + app,
            r"talk.*" + app,
            r"helpful.*" + app,
            r"good.*" + app,
            r"privacy.*" + app,
            r"security.*" + app,
        ]

        for pattern in negative_patterns:
            if re.search(pattern, text_lower):
                return False  # Not a promotion

        # If negative patterns not found, treat as promotion/scam by default
        # This is conservative: flag anything with contact app unless explicitly not promotional
        return True

    def analyze_context(self, text: str) -> dict:
        """
        Use zero-shot classification to understand context.
        Returns likelihood of scam context vs legitimate context.
        """
        if self.classifier is None:
            return {"is_scam_context": False, "confidence": 0.0}

        # Updated candidate labels for better scam detection
        candidate_labels = [
            "trying to get someone to contact them",
            "warning about dangers",
            "general discussion about an app",
            "sharing personal preference",
        ]

        try:
            result = self.classifier(text, candidate_labels, multi_class=False)
            top_label = result["labels"][0]
            top_score = result["scores"][0]

            # Scam-related labels - when someone is trying to get contact
            scam_labels = ["trying to get someone to contact them"]
            is_scam_context = top_label in scam_labels

            return {
                "is_scam_context": is_scam_context,
                "confidence": top_score,
                "top_label": top_label,
                "all_scores": dict(zip(result["labels"], result["scores"])),
            }
        except Exception as e:
            print(f"[ERROR] Context analysis failed: {e}")
            return {"is_scam_context": False, "confidence": 0.0}

    def calculate_scam_score(self, keywords_detected: dict, context_analysis: dict) -> tuple[float, str]:
        """
        Calculate final scam score (0-100) based on:
        - Keywords detection: 0-70 points (higher if multiple apps detected)
        - Context analysis: -40 to +50 adjustment
        - Presence of contact request patterns

        Returns (score, reason)
        """
        base_score = 0
        reason_parts = []

        # Keyword-based score
        if keywords_detected:
            max_confidence = max(keywords_detected.values())
            num_apps = len(keywords_detected)

            # Base score increases with number of detected apps
            base_score = max_confidence * 70 + (num_apps - 1) * 10  # 0-100 if multiple apps

            apps_found = ", ".join(keywords_detected.keys())
            reason_parts.append(f"Found contact app(s): {apps_found}")

        # Context-based adjustment
        if context_analysis.get("is_scam_context"):
            # Positive adjustment if scam context detected
            adjustment = context_analysis.get("confidence", 0) * 50
            base_score += adjustment
            reason_parts.append(f"Scam-like intent detected (confidence: {context_analysis['confidence']:.2f})")
        else:
            # Negative adjustment if NOT scam context
            # But don't reduce too much if keywords are present
            if keywords_detected:
                # For messages with contact apps but non-scam context, reduce by half
                adjustment = -context_analysis.get("confidence", 0) * 20
                base_score = max(30, base_score + adjustment)  # Keep minimum score of 30 if app detected
                if adjustment < 0:
                    reason_parts.append(
                        f"But context seems legitimate (confidence: {context_analysis.get('confidence', 0):.2f})"
                    )
            else:
                # No keywords detected, reduce score significantly
                adjustment = -context_analysis.get("confidence", 0) * 40
                base_score = max(0, base_score + adjustment)

        final_score = max(0, min(100, base_score))
        reason = " | ".join(reason_parts) if reason_parts else "No scam indicators detected"

        return final_score, reason

    def detect(self, message: str, language: str = "en") -> dict:
        """
        Main detection method.

        Args:
            message: The message text to analyze
            language: Language code ('en', 'es', 'vi')

        Returns:
            {
                'is_scam': bool,
                'scam_score': float (0-100),
                'reason': str,
                'keywords_found': dict,
                'context': dict
            }
        """
        # Detect keywords
        keywords_detected = self.detect_keywords(message, language)

        # Only do context analysis if keywords are detected
        context_analysis = {}
        if keywords_detected:
            context_analysis = self.analyze_context(message)
        else:
            context_analysis = {"is_scam_context": False, "confidence": 0.0}

        # Calculate score
        scam_score, reason = self.calculate_scam_score(keywords_detected, context_analysis)

        # Threshold for classification
        is_scam = scam_score >= 50

        return {
            "is_scam": is_scam,
            "scam_score": round(scam_score, 2),
            "reason": reason,
            "keywords_found": keywords_detected,
            "context": context_analysis,
            "language": language,
        }
