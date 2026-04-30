import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline import answer
from app.models.chat import ChatSession, ChatMessage
from app.api.schemas import ChatRequest, ChatResponse, SourceItem


async def handle_chat(request: ChatRequest, db: AsyncSession) -> ChatResponse:
    """
    Xử lý một lượt chat:
      1. Tạo hoặc lấy ChatSession
      2. Gọi RAG pipeline
      3. Lưu cặp (user message, assistant message) vào Postgres
      4. Trả về ChatResponse
    """
    # 1. Session
    session_id = request.session_id
    if session_id:
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        chat_session = (await db.execute(stmt)).scalar_one_or_none()
        if chat_session is None:
            chat_session = _create_session(request)
            db.add(chat_session)
    else:
        chat_session = _create_session(request)
        db.add(chat_session)
        session_id = chat_session.id

    # 2. Lưu user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.query,
    )
    db.add(user_msg)

    # 3. Gọi pipeline
    result = await answer(
        query=request.query,
        user_id=str(request.user_id) if request.user_id else None,
    )

    # 4. Lưu assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
    )
    db.add(assistant_msg)
    await db.commit()

    # 5. Build response
    sources = [
        SourceItem(
            title=s.get("title"),
            published_date=str(s.get("published_date") or "")[:10] or None,
            source=s.get("source"),
            rerank_score=s.get("rerank_score"),
        )
        for s in result.get("sources", [])
    ]

    return ChatResponse(
        answer=result["answer"],
        session_id=session_id,
        sources=sources,
        entities=result.get("entities", []),
        job_titles=result.get("job_titles", []),
        query=request.query,
    )


def _create_session(request: ChatRequest) -> ChatSession:
    title = request.query[:80] if request.query else "Cuộc hội thoại mới"
    return ChatSession(
        id=uuid.uuid4(),
        user_id=request.user_id or uuid.UUID(int=0),
        title=title,
    )
