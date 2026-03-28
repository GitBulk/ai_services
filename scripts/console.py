import os
import sys

import IPython
from traitlets.config import Config

from app.core.settings import settings
from app.db.qdrant_db import get_qdrant_db
from app.db.session import SessionLocal, engine
from app.dependencies.ai_model import get_ai_model_registry
from app.dependencies.repositories import get_product_repository, get_product_vector_repository
from app.dependencies.services import get_product_service
from app.models.blue_green_config import BlueGreeConfig

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

# Khởi tạo Context (Các biến dùng trực tiếp trong shell)
db = SessionLocal()
# nova = NovaAIClassifier()  # Nạp sẵn model DeBERTa
qdrant_db = get_qdrant_db()
product_repo = get_product_repository(db)
vector_repo = get_product_vector_repository(qdrant_db)
print("🧠 Đang nạp AI Models vào RAM (Vui lòng đợi vài giây)...")
ai_model = get_ai_model_registry()
ai_model.load_models()
ai_model.use_model("clip_embedding")
product_service = get_product_service(product_repo, vector_repo, ai_model)
# Dictionary chứa các biến sẽ nạp vào shell
# Bạn gõ tên key nào thì nó ra object đó (vd: gõ User sẽ ra class User)
namespace = {
    "db": db,
    "session": db,  # Alias cho quen thuộc
    "BlueGreeConfig": BlueGreeConfig,
    # "Message": Message,
    # "Training": NovaTrainingData,
    # "NovaAIClassifier": nova,  # Load luôn bộ não AI vào RAM
    # "qdrant_db": qdrant_db,
    "product_service": product_service,
    "debug": debug,
    "settings": settings,
    "os": os,
    "engine": engine,
}

# Cấu hình giao diện Shell
c = Config()
c.InteractiveShellApp.exec_lines = [
    'print("-" * 50)',
    'print("🚀 NOVA AI CONSOLE (Rails-style) READY")',
    'print("Usage: db.query(User).first()")',
    'print("-" * 50)',
]
c.TerminalInteractiveShell.confirm_exit = False
c.TerminalInteractiveShell.sql_color = True


# Đảm bảo đóng session khi thoát console (giống cleanup)
def close_db():
    db.close()
    print("\n👋 Database session closed. Goodbye!")


# Chạy IPython
if __name__ == "__main__":
    try:
        IPython.start_ipython(argv=[], user_ns=namespace, config=c)
    except Exception as e:
        print(f"❌ Lỗi khi chạy console: {e}")
    finally:
        close_db()
