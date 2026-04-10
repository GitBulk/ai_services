import importlib
import os
import re
from datetime import datetime

import typer
from qdrant_client import models

from app.core.time.service import DateTimeService
from app.db.migrations_qdrant.base import QdrantMigrationError
from app.db.qdrant_db import get_qdrant_db

app = typer.Typer(help="Qdrant Migration Tool")
HISTORY_COLLECTION = "qdrant_versions"
qdrant_db = get_qdrant_db()


def snake_to_camel(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def ensure_history_collection():
    """Đảm bảo collection lưu lịch sử tồn tại"""
    if not qdrant_db.collection_exists(HISTORY_COLLECTION):
        # Dummy Vector Config
        qdrant_db.create_collection(
            collection_name=HISTORY_COLLECTION,
            vectors_config=models.VectorParams(size=1, distance=models.Distance.COSINE),
        )
        typer.echo(f"📦 Created history collection: {HISTORY_COLLECTION}")


@app.callback()
def callback():
    """Qdrant Migration CLI tool."""
    pass


@app.command("migrate")
def migrate(
    message: str = typer.Option(None, "--message", "-m", help="Tạo file migration mới"),
    up: bool = typer.Option(False, "--up", help="Chạy nâng cấp database"),
):
    """Tạo một file migration mới với timestamp"""
    if message:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        clean_msg = re.sub(r"[^a-zA-Z0-9]", "_", message.lower())
        filename = f"{timestamp}_{clean_msg}.py"
        class_name = snake_to_camel(clean_msg)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        versions_dir = os.path.join(current_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)
        target_path = os.path.join(versions_dir, filename)

        template = f"""from qdrant_client import QdrantClient, models
from app.db.migrations_qdrant.base import QdrantMigration

class {class_name}(QdrantMigration):
    def up(self):
        # self.create_col("collection_name", size=768)
        pass

    def down(self):
        # self.drop_col("collection_name")
        pass
"""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(template)

        typer.secho(f"🚀 Generated: {target_path}", fg=typer.colors.GREEN)
        typer.secho(f"💎 Class: {class_name}", fg=typer.colors.CYAN)
        return

    if up:
        ensure_history_collection()
        points, _ = qdrant_db.scroll(collection_name=HISTORY_COLLECTION, limit=1000)
        applied_versions = [str(p.id) for p in points]
        current_dir = os.path.dirname(os.path.abspath(__file__))
        versions_dir = os.path.join(current_dir, "versions")
        if not os.path.exists(versions_dir):
            typer.echo("Chưa có thư mục versions.")
            return

        files = sorted([f for f in os.listdir(versions_dir) if f.endswith(".py")])
        applied_count = 0
        for filename in files:
            version_id = filename.split("_")[0]

            if version_id not in applied_versions:
                typer.echo(f"Applying {filename}...")

                # Import động
                file_path = os.path.join(versions_dir, filename)
                spec = importlib.util.spec_from_file_location(f"migration_{version_id}", file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Tìm class theo naming convention (Snake_to_Camel)
                clean_name = "_".join(filename.replace(".py", "").split("_")[1:])
                class_name = snake_to_camel(clean_name)

                try:
                    migration_class = getattr(module, class_name)
                    instance = migration_class(qdrant_db)

                    # THỰC THI
                    instance.up()

                    # LƯU VẾT (Chỉ khi up thành công)
                    int_version_id = int(version_id)
                    payload = {
                        "version": int_version_id,
                        "name": filename,
                        # "applied_at": datetime.now(timezone.utc).isoformat(),
                        "applied_at": DateTimeService.now_rfc3339(),
                    }
                    qdrant_db.upsert(
                        collection_name=HISTORY_COLLECTION,
                        points=[models.PointStruct(id=int_version_id, vector=[0.0], payload=payload)],
                    )
                    applied_count += 1
                    typer.secho(f"✅ Successfully applied {version_id}", fg=typer.colors.GREEN)

                except QdrantMigrationError as err:
                    typer.secho(f"❌ Migration logic error: {str(err)}", fg=typer.colors.RED, bold=True)
                    raise typer.Exit(code=1) from err

                except Exception as err:
                    # Nếu là lỗi hệ thống không xác định, ta cũng nên 'from err'
                    typer.secho(f"🔥 Unexpected System Error: {str(err)}", fg=typer.colors.RED)
                    raise typer.Exit(code=1) from err

        if applied_count == 0:
            typer.echo("✨ Database is already up to date.")

        return

    qdrant_db.close()
    typer.echo("Sử dụng --help để xem hướng dẫn. Ví dụ: qdrant migrate -m 'init'")


if __name__ == "__main__":
    app()
