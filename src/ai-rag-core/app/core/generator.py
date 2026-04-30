import asyncio
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings

_MAX_RETRIES = 3
_RETRY_DELAY = 5  # seconds


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    """Khởi tạo Gemini LLM một lần duy nhất."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.2,
    )


async def generate(messages: list[dict]) -> str:
    """
    Gọi Gemini và trả về text câu trả lời.
    Tự retry khi gặp lỗi 503 (server bận).

    messages: output của prompt_builder.build_messages()
              [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    llm = get_llm()

    lc_messages = []
    for m in messages:
        if m["role"] == "system":
            lc_messages.append(SystemMessage(content=m["content"]))
        else:
            lc_messages.append(HumanMessage(content=m["content"]))

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = await llm.ainvoke(lc_messages)
            return response.content

        except Exception as e:
            err = str(e).lower()
            if ("503" in err or "service unavailable" in err or "overloaded" in err) and attempt < _MAX_RETRIES:
                print(f"  [generator] server bận, thử lại sau {_RETRY_DELAY}s (lần {attempt}/{_MAX_RETRIES})...")
                await asyncio.sleep(_RETRY_DELAY)
            else:
                raise RuntimeError(f"Gemini lỗi: {e}") from e
