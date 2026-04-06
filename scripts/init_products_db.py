import json

from sqlalchemy import text

from app.db.session import engine

JSONL_FILE = "/Users/mingle/Documents/mingle/rails7/rails7/tmp/products_for_ai_20260328_141516.jsonl"


def insert_batch_jsonl():
    data_list = []
    print(f"engine.url: {engine.url}")
    print(f"📂 Đang đọc file: {JSONL_FILE}...")

    with open(JSONL_FILE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():  # Bỏ qua dòng trống
                continue
            d = json.loads(line)
            data_list.append(
                {
                    "id": d.get("id"),
                    "image_path": d.get("image_path"),
                    "gender": d.get("gender"),
                    "master_category": d.get("master_category"),
                    "sub_category": d.get("sub_category"),
                    "article_type": d.get("article_type"),
                    "base_colour": d.get("base_colour"),
                    "season": d.get("season"),
                    "year": d.get("year"),
                    "usage": d.get("usage"),
                    "product_display_name": d.get("product_display_name"),
                    "price": float(d.get("price", 0)),
                    "brand": d.get("brand"),
                    "text_for_ai": d.get("text_for_ai"),
                }
            )

    query = text("""
        INSERT INTO products (
            id, image_path, gender, master_category, sub_category, 
            article_type, base_colour, season, year, usage, 
            product_display_name, price, brand, text_for_ai
        ) VALUES (
            :id, :image_path, :gender, :master_category, :sub_category, 
            :article_type, :base_colour, :season, :year, :usage, 
            :product_display_name, :price, :brand, :text_for_ai
        )
    """)

    print(f"🚀 Đang đẩy {len(data_list)} dòng vào Postgres 18...")
    with engine.begin() as conn:
        conn.execute(query, data_list)

    print(f"✅ Thành công! Đã nạp {len(data_list)} sản phẩm cho Nova AI.")


if __name__ == "__main__":
    insert_batch_jsonl()
