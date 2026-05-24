import asyncio
import os

from openai import AsyncOpenAI, RateLimitError

from services.rate_limit import rate_limiter
from services.usage_context import get_user

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client: AsyncOpenAI | None = None
_max_concurrent = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "3"))


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to backend/.env or the repo-root .env."
            )
        _client = AsyncOpenAI(api_key=api_key)
    return _client


_semaphore = asyncio.Semaphore(_max_concurrent)


def _record_usage(response) -> None:
    user_id = get_user()
    usage = getattr(response, "usage", None)
    if not user_id or not usage:
        return
    total = (usage.prompt_tokens or 0) + (usage.completion_tokens or 0)
    rate_limiter.record_tokens(user_id, total)


async def create_message(
    *,
    messages: list[dict],
    max_tokens: int,
    model: str | None = None,
    max_retries: int = 5,
    json_mode: bool = False,
):
    model = model or DEFAULT_MODEL
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        async with _semaphore:
            try:
                response = await _get_client().chat.completions.create(**kwargs)
                _record_usage(response)
                return response
            except RateLimitError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(min(2 ** attempt + 1, 30))
    raise RuntimeError("Rate limit exceeded after retries")
