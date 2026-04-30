from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ChatRequest, ChatResponse
from app.db.postgres_client import get_session
from app.services.chat_service import handle_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """
    Gửi câu hỏi, nhận câu trả lời từ RAG pipeline.

    - `query`: câu hỏi của user
    - `session_id`: UUID phiên hội thoại (None để tạo mới)
    - `user_id`: UUID user đã đăng nhập (None nếu ẩn danh)
    """
    try:
        return await handle_chat(request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
