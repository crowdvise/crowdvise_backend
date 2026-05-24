from contextvars import ContextVar

_llm_user_id: ContextVar[str | None] = ContextVar("llm_user_id", default=None)


def set_user(user_id: str | None) -> None:
    _llm_user_id.set(user_id)


def get_user() -> str | None:
    return _llm_user_id.get()
