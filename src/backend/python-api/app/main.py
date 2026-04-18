from fastapi import FastAPI

from app.core.config import get_settings
from app.routers.llm import router as llm_router
from app.routers.ocr import router as ocr_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Internal AI service for TechPulse backend",
)

app.include_router(llm_router)
app.include_router(ocr_router)


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "python-ai",
        "environment": settings.app_env,
    }


@app.get("/internal/health")
async def internal_health() -> dict:
    return {
        "status": "ok",
        "postgres_configured": bool(settings.postgres_connection_string),
    }

