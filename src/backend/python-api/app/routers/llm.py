from fastapi import APIRouter

router = APIRouter(prefix="/internal/ai", tags=["llm"])


@router.get("/llm/health")
async def llm_health() -> dict:
    return {"status": "ready", "component": "llm"}
