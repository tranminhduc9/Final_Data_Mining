from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_embed import router as embed_router
from app.api.routes_health import router as health_router
from app.db.neo4j_client import close_driver
from app.db.postgres_client import close_engine, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — Postgres optional (RAG core vẫn chạy khi Postgres down)
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
