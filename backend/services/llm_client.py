import asyncio
import os
from anthropic import AsyncAnthropic, RateLimitError

client = AsyncAnthropic()
_max_concurrent = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "3"))
_semaphore = asyncio.Semaphore(_max_concurrent)


async def create_message(*, max_retries: int = 5, **kwargs):
    for attempt in range(max_retries):
        async with _semaphore:
            try:
                return await client.messages.create(**kwargs)
            except RateLimitError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(min(2 ** attempt + 1, 30))
    raise RateLimitError("Rate limit exceeded after retries")
