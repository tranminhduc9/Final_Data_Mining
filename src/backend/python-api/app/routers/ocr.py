from fastapi import APIRouter

router = APIRouter(prefix="/internal/ai", tags=["ocr"])


@router.get("/ocr/health")
async def ocr_health() -> dict:
    return {"status": "ready", "component": "ocr"}
