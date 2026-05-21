import os


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")


class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    auth_disabled: bool = _env_bool("AUTH_DISABLED", False)

    allowed_origins: list[str] = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
        if o.strip()
    ]

    max_request_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", "1048576"))

    rate_limit_generate_stages: int = int(os.getenv("RATE_LIMIT_GENERATE_STAGES", "30"))
    rate_limit_run: int = int(os.getenv("RATE_LIMIT_RUN", "10"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))


settings = Settings()


def validate_settings() -> None:
    if settings.auth_disabled:
        return
    missing = []
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise RuntimeError(
            f"Missing required env vars: {', '.join(missing)}. "
            "Set them for Supabase auth, or AUTH_DISABLED=true for local dev only."
        )
