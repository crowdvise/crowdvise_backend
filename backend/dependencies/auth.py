from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from config import settings
from services.rate_limit import rate_limiter

security = HTTPBearer(auto_error=not settings.auth_disabled)


@dataclass
class AuthUser:
    id: str
    email: str | None = None


@lru_cache
def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _verify_token(token: str) -> AuthUser:
    try:
        response = get_supabase().auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None

    if not response or not response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return AuthUser(id=response.user.id, email=response.user.email)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    if settings.auth_disabled:
        return AuthUser(id="dev-local", email="dev@local")

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    return _verify_token(credentials.credentials)


async def require_generate_stages_limit(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    rate_limiter.check(
        key=f"generate-stages:{user.id}",
        max_calls=settings.rate_limit_generate_stages,
        window_seconds=settings.rate_limit_window_seconds,
    )
    return user


async def require_run_limit(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    rate_limiter.check(
        key=f"run:{user.id}",
        max_calls=settings.rate_limit_run,
        window_seconds=settings.rate_limit_window_seconds,
    )
    return user


async def require_history_limit(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    rate_limiter.check(
        key=f"history:{user.id}",
        max_calls=settings.rate_limit_history,
        window_seconds=settings.rate_limit_window_seconds,
    )
    return user
