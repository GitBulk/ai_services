# app/db/tortoise_config.py

from app.core.settings import settings

database_url = settings.database_url
print(f"[INFO] DB URL: {database_url}")
TORTOISE_CONFIG = {
    "connections": {
        "default": database_url,  # Đảm bảo settings trả về đúng chuỗi postgres://
        # "analytics": "...",
        # "replica": "...",
    },
    "apps": {
        "models": {
            # Quét toàn bộ folder models
            "models": ["app.models"],
            "default_connection": "default",
        }
    },
}
