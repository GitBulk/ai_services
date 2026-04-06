from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

# from app.services.vector_resource_manager import VectorResourceManager
from app.core.model_registry import model_registry
from app.core.settings import settings
from app.db.qdrant_db import qdrant_db
from app.db.tortoise_config import TORTOISE_CONFIG
from app.routes import router as nova_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Starting Nova AI...")
    # Load model AI nặng trịch vào RAM
    model_registry.load_models()
    model_registry.use_model("clip_embedding")
    print("[INFO] Nova AI ready 🚀")
    # await Tortoise.init(config=TORTOISE_CONFIG)
    # async with RegisterTortoise(
    #     app=app,                    # important: pass the app
    #     config=TORTOISE_CONFIG
    # ):
    # print("[INFO] DB connected")
    # yield

    # yield
    async with RegisterTortoise(
        app=app,
        config=TORTOISE_CONFIG,  # hoặc db_url + modules
        generate_schemas=False,  # Chỉ bật True khi dev và muốn tự tạo bảng
        add_exception_handlers=True,
    ):
        print("[INFO] DB connected")
        yield  # ← Phải có yield ở đây

    # Cleanup khi tắt server
    print("[INFO] Shutting down...")
    # await Tortoise.close_connections()
    qdrant_db.close()
    print("[INFO] DB closed")


app = FastAPI(title=settings.PROJECT_NAME, description="Nova AI", version="1.0", lifespan=lifespan)

# add middlewares
# app.add_middleware(TracingMiddleware)
app.include_router(nova_router, prefix="/api/v1", tags=["Nova Analysis"])


@app.get("/")
async def root():
    return {
        "message": "Nova AI Service is running",
        "device": settings.DEVICE,
        "project": "#nova_ai",
        "version": settings.VERSION,
    }
