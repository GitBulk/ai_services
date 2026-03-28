import datetime
import json
import time

from qdrant_client import models

from app.core.model_registry import model_registry
from app.core.settings import settings
from app.db.qdrant_db import get_qdrant_db
from app.dependencies.repositories import get_product_vector_repository

JSONL_FILE = "/Users/mingle/Documents/mingle/rails7/rails7/tmp/products_for_ai_20260328_141516.jsonl"
BATCH_SIZE = 100
IMAGE_BASE_PATH = "/Users/mingle/Documents/mingle/rails7/rails7/tmp/kaggle_data/images/"


def run_import():
    print("🚀 Bắt đầu quá trình đưa sản phẩm lên Qdrant Cloud...")
    qdrant_db = get_qdrant_db()
    utc_now = datetime.now(datetime.timezone.utc)
    # version có dạng 20260328_141516
    new_collection_name = f"{settings.QDRANT_ENVIRONMENT}_nova_products_{utc_now.strftime('%Y%m%d_%H%M%S')}"
    vector_repo = get_product_vector_repository(qdrant_db)
    alias_name = vector_repo.current_alias_name
    model_registry.load_models()
    model_registry.use_model("clip_embedding")
    print(f"📦 Đang tạo collection '{new_collection_name}' trên Qdrant Cloud...")
    vector_repo.create_collection(new_collection_name)
    print(f"🔄 Đang trỏ Alias '{alias_name}' ---> Collection '{new_collection_name}'...")
    vector_repo.create_alias_with_collection(new_collection_name)
    # Tạm thời trỏ Repo vào collection mới để tận dụng hàm upsert_batch
    vector_repo.collection_name = new_collection_name
    batch_points = []
    total_imported = 0
    start_time = time.time()
    print("🔥 Đang sync data vào vùng không gian mới (Hệ thống Live không bị ảnh hưởng)...")
    with open(JSONL_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                product = json.loads(line)
                text_for_ai = product.get("text_for_ai", "")
                text_vector = model_registry.encode_text(text_for_ai)
                image_path = product.get("image_path", "")
                real_image_path = f"{IMAGE_BASE_PATH}{image_path}"
                image_vector = model_registry.encode_image(real_image_path)

                points_vector = {"text_vector": text_vector, "image_vector": image_vector}
                payload = {key: value for key, value in product.items() if key not in ["text_for_ai", "image_path"]}
                point = models.PointStruct(id=product["id"], vector=points_vector, payload=payload)
                batch_points.append(point)
                # push lên Qdrant theo batch để tối ưu tốc độ, tránh push từng điểm sẽ rất chậm
                if len(batch_points) >= BATCH_SIZE:
                    vector_repo.upsert_batch(batch_points)
                    total_imported += len(batch_points)
                    elapsed = time.time() - start_time
                    print(f"✅ Đã import {total_imported} sản phẩm... (Elapsed: {elapsed:.2f}s)")
                    batch_points = []
            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý sản phẩm ID {product['id']}: {e}")

    # batch cuối
    if batch_points:
        vector_repo.upsert_batch(batch_points)
        total_imported += len(batch_points)

    print(f"ZERO-DOWNTIME HOÀN TẤT! Đã đẩy {total_imported} vectors trong {time.time() - start_time:.2f} giây!")


if __name__ == "__main__":
    run_import()
