import argparse

from app.db.qdrant_db import get_qdrant_db
from app.dependencies.repositories import get_product_vector_repository


# usage:
# python scripts/rollback_products_qdrant.py --version 20260328_141516
# python scripts/rollback_products_qdrant.py --help
def run_rollback(version: str):
    print("⏪ Bắt đầu quá trình rollback về collection cũ trên Qdrant Cloud...")
    qdrant_db = get_qdrant_db()
    vector_repo = get_product_vector_repository(qdrant_db)
    alias_name = vector_repo.collection_name
    new_collection_name = f"{alias_name}_{version}"
    vector_repo.switch_alias(new_collection_name)
    qdrant_db.close()
    print(f"✅ Đã rollback về collection '{new_collection_name}' trên Qdrant Cloud.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rollback Qdrant collection về phiên bản cũ")
    parser.add_argument(
        "--version", type=str, required=True, help="Timestamp của collection cũ (ví dụ: 20260328_141516 hoặc 20260328)"
    )
    args = parser.parse_args()
    run_rollback(args.version)
