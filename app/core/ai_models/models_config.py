from app.core.ai_models.multi_modal_specialist import MultiModalSpecialist
from app.core.ai_models.text_specialist import TextSpecialist
from app.core.config import settings

MODEL_DEFINITIONS = {
    "vi-text-fast": {
        "provider_cls": TextSpecialist,
        "config": {
            "model_id": "all-MiniLM-L6-v2",
            "device": settings.DEVICE,
        },
    },
    "clip-multimodal": {
        "provider_cls": MultiModalSpecialist,
        "config": {
            "model_id": "clip-ViT-B-32",
            "device": settings.DEVICE,
        },
    },
}
