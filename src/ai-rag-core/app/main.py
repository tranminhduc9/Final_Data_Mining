import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_embed import router as embed_router
from app.api.routes_health import router as health_router
from app.db.neo4j_client import close_driver
from app.db.postgres_client import close_engine, create_tables


def _warmup_models() -> None:
    """Load E5 embedder + CrossEncoder reranker vào RAM lúc startup.
    Chạy trong thread pool để không block async event loop.
    """
    from app.core.embedder import get_embedder
    from app.core.reranker import get_reranker
    print("[Startup] Loading embedding model...")
    get_embedder()
    print("[Startup] Loading reranker model...")
    get_reranker()
    print("[Startup] Models ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm-up models trong thread pool (CPU-bound, không block event loop)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warmup_models)

    # Postgres optional (RAG core vẫn chạy khi Postgres down)
    try:
        await create_tables()
    except Exception as e:
        print(f"[WARNING] Postgres không kết nối được: {e}. Chat history sẽ không được lưu.")
    yield
    # Shutdown
    await close_driver()
    await close_engine()


app = FastAPI(
    title="TechPulse RAG Service",
    description="RAG pipeline phân tích xu hướng công nghệ IT Việt Nam",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(embed_router)
