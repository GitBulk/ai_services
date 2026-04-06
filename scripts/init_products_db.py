import asyncio
import json

from tortoise import Tortoise

from app.db.tortoise_config import TORTOISE_CONFIG

JSONL_FILE = "/Users/mingle/Documents/mingle/rails7/rails7/tmp/products_for_ai_20260328_141516.jsonl"


async def insert_batch_jsonl():
    data_list = []
    sql = """
        INSERT INTO products (
            id, image_path, gender, master_category, sub_category,
            article_type, base_colour, season, year, usage,
            product_display_name, price, brand, text_for_ai
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    """
    print("🐢 Đang sử dụng Tortoise-ORM kết nối Postgres...")
    print(f"📂 Đang đọc file: {JSONL_FILE}...")
    batch_size = 2000
    total_count = 0
    await Tortoise.init(config=TORTOISE_CONFIG)
    conn = Tortoise.get_connection("default")
    with open(JSONL_FILE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():  # Bỏ qua dòng trống
                continue
            d = json.loads(line)
            row = (
                d.get("id"),
                d.get("image_path"),
                d.get("gender"),
                d.get("master_category"),
                d.get("sub_category"),
                d.get("article_type"),
                d.get("base_colour"),
                d.get("season"),
                d.get("year"),
                d.get("usage"),
                d.get("product_display_name"),
                float(d.get("price") or 0),
                d.get("brand"),
                d.get("text_for_ai"),
            )
            data_list.append(row)
            count_new = len(data_list)

            if count_new >= batch_size:
                await conn.execute_many(sql, data_list)
                total_count += count_new
                print(f"🚀 Đã nạp: {total_count} dòng...")
                data_list = []

    if data_list:
        await conn.execute_many(sql, data_list)
        total_count += len(data_list)

    print(f"✅ Thành công! Đã nạp {total_count} sản phẩm cho Nova AI.")

    # 2. ĐỒNG BỘ SEQUENCE (Cực kỳ quan trọng vì ông insert kèm ID)
    # Nếu không làm bước này, lần tới ông dùng .create() sẽ bị lỗi Duplicate ID
    conn = Tortoise.get_connection("default")
    await conn.execute_script(
        "SELECT setval(pg_get_serial_sequence('products', 'id'), coalesce(max(id), 0) + 1, false) FROM products;"
    )
    print("🔧 Đã đồng bộ Postgres Sequence cho cột ID.")
    # Đóng kết nối
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(insert_batch_jsonl())
