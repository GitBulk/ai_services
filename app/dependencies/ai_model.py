from app.core.model_registry import ModelRegistry, model_registry


def get_ai_model_registry() -> ModelRegistry:
    # Trả về Singleton ModelRegistry đã được load sẵn từ hàm lifespan trong main.py.
    # Không khởi tạo lại model ở đây!
    return model_registry
