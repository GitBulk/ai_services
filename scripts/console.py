import os
import sys

import IPython
from traitlets.config import Config

from app.core.config import settings
from app.db.qdrant_db import get_qdrant_db
from app.db.session import SessionLocal, engine
from app.dependencies.ai_model import get_ai_model_registry
from app.dependencies.repositories import get_product_repository, get_product_vector_repository
from app.dependencies.services import get_product_service
from app.models.blue_green_config import BlueGreeConfig
from app.models.scoring_profile import ScoringProfile

# Thêm thư mục gốc của project vào sys.path để import được app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- 1. Import các thành phần core, nạp environment ---
try:
    # from app.db.session import SessionLocal, engine
    # from app.models.message import Message
    # from app.models.training import NovaTrainingData
    # from app.models.user import User
    # Thêm công cụ debug để in dữ liệu đẹp hơn rails c
    from devtools import debug

    # from app.ai.nova_ai_classifier import NovaAIClassifier
except ImportError as e:
    print(f"❌ Lỗi nạp Model/DB: {e}")
    print("Hãy đảm bảo bạn đã cài đặt các thư viện và cấu trúc folder đúng.")


def create_console_namespace():
    """Tạo các object sẵn để dùng trong console"""
    db = SessionLocal()

    qdrant_db = get_qdrant_db()
    product_repo = get_product_repository(db)
    vector_repo = get_product_vector_repository(qdrant_db)

    print("🧠 Đang load AI models (có thể mất vài giây)...")
    ai_registry = get_ai_model_registry()
    ai_registry.load_models()
    ai_registry.use_model("clip_embedding")

    product_service = get_product_service(product_repo, vector_repo, ai_registry)

    namespace = {
        "db": db,
        "session": db,
        "engine": engine,
        "settings": settings,
        "qdrant_db": qdrant_db,
        "product_repo": product_repo,
        "vector_repo": vector_repo,
        "product_service": product_service,
        "ai_model": ai_registry,
        "BlueGreeConfig": BlueGreeConfig,
        "ScoringProfile": ScoringProfile,
        "debug": debug,
        "os": os,
    }

    return namespace, db


def main():
    namespace, db = create_console_namespace()

    c = Config()
    c.InteractiveShellApp.exec_lines = [
        "%load_ext autoreload",  # Load extension
        "%autoreload 2",  # Bật chế độ reload tất cả modules
        'print("-" * 50)',
        'print("🚀 NOVA AI CONSOLE READY")',
        'print("-" * 50)',
    ]
    c.TerminalInteractiveShell.confirm_exit = False
    c.TerminalInteractiveShell.sql_color = True
    print("Đang khởi động IPython...")
    try:
        IPython.start_ipython(argv=[], user_ns=namespace, config=c)
    except KeyboardInterrupt:
        print("\n👋 Đã thoát bằng Ctrl+C")
    except Exception as e:
        print(f"❌ Lỗi khi chạy IPython console: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            db.close()
            print("✅ Database session đã đóng.")
        except Exception as close_e:
            print(f"⚠️ Không đóng được DB session: {close_e}")
            pass


if __name__ == "__main__":
    main()
