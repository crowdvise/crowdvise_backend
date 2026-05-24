from fastapi import APIRouter, Depends, HTTPException

from config import settings
from dependencies.auth import AuthUser, get_current_user
from models import UserProfileResponse, UserProfileUpsertRequest
from services.profile_store import (
    ProfileStoreError,
    get_profile,
    handle_profile_store_error,
    upsert_profile,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _require_profile_auth() -> None:
    if settings.auth_disabled:
        raise HTTPException(
            status_code=400,
            detail=(
                "Profile endpoints require authentication. Set AUTH_DISABLED=false and "
                "send Authorization: Bearer <supabase_access_token>."
            ),
        )


@router.get("", response_model=UserProfileResponse)
async def read_profile(
    user: AuthUser = Depends(get_current_user),
) -> UserProfileResponse:
    _require_profile_auth()
    try:
        profile = get_profile(user.id)
    except ProfileStoreError as exc:
        raise handle_profile_store_error(exc) from exc

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Complete signup via PUT /profile.",
        )
    return profile


@router.put("", response_model=UserProfileResponse)
async def complete_or_update_profile(
    body: UserProfileUpsertRequest,
    user: AuthUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Create or update profile after Supabase signup (first name, last name, industry)."""
    _require_profile_auth()
    try:
        return upsert_profile(user.id, user.email, body)
    except ProfileStoreError as exc:
        raise handle_profile_store_error(exc) from exc
