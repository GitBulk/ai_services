from fastapi import FastAPI
from app.routes import router as nova_router
from app.core import settings

app = FastAPI(
    title = settings.PROJECT_NAME,
    description = "Nova AI",
    version = "1.0"
)

app.include_router(nova_router, prefix = "/api/v1", tags = ["Nova Analysis"])

@app.get("/")
async def root():
    return {
        "message": "Nova AI Service is running",
        "device": settings.DEVICE,
        "project": "#nova_ai",
        "version": settings.VERSION
    }