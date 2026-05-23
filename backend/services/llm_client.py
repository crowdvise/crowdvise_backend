import asyncio
import os

from openai import AsyncOpenAI, RateLimitError

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


async def create_message(
    *,
    messages: list[dict],
    max_tokens: int,
    model: str | None = None,
    max_retries: int = 5,
):
    model = model or DEFAULT_MODEL

    for attempt in range(max_retries):
        async with _semaphore:
            try:
                return await _get_client().chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                )
            except RateLimitError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(min(2 ** attempt + 1, 30))
    raise RuntimeError("Rate limit exceeded after retries")
