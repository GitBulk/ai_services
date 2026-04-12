from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from app.core.ai_models.model_manager import model_manager
from app.core.ai_models.models_config import MODEL_DEFINITIONS
from app.core.config import settings
from app.core.redis import close_redis_async, get_async_redis_client
from app.db.qdrant_db import close_qdrant_client_async, get_async_qdrant_db
from app.db.tortoise_config import TORTOISE_CONFIG
from app.routes import router as nova_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Starting Nova AI...")
    model_manager.load_definitions(MODEL_DEFINITIONS)
    await model_manager.warm_up()
    get_async_qdrant_db()
    get_async_redis_client()
    async with RegisterTortoise(
        app=app,
        config=TORTOISE_CONFIG,
        generate_schemas=settings.GENERATE_SCHEMAS,
        add_exception_handlers=True,
    ):
        print("[INFO] Nova AI ready")
        yield

    print("[INFO] Shutting down...")
    await close_qdrant_client_async()
    await close_redis_async()
    await model_manager.clear_all()
    print("[INFO] Shutdown complete")


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
