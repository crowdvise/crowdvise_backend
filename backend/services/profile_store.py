from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from dependencies.auth import get_supabase
from models import UserProfileResponse, UserProfileUpsertRequest


class ProfileStoreError(Exception):
    pass


def _table_missing(exc: Exception) -> bool:
    detail = str(exc)
    return "profiles" in detail and ("does not exist" in detail or "PGRST205" in detail)


def get_profile(user_id: str) -> UserProfileResponse | None:
    try:
        response = (
            get_supabase()
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise ProfileStoreError(str(exc)) from exc

    rows = response.data or []
    if not rows:
        return None
    return _row_to_response(rows[0])


def upsert_profile(
    user_id: str,
    email: str | None,
    body: UserProfileUpsertRequest,
) -> UserProfileResponse:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": user_id,
        "email": email,
        "first_name": body.first_name.strip(),
        "last_name": body.last_name.strip(),
        "industry": body.industry.strip(),
        "updated_at": now,
    }
    try:
        existing = (
            get_supabase()
            .table("profiles")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            get_supabase().table("profiles").update(
                {
                    "email": email,
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "industry": row["industry"],
                    "updated_at": now,
                }
            ).eq("id", user_id).execute()
        else:
            row["created_at"] = now
            get_supabase().table("profiles").insert(row).execute()
    except Exception as exc:
        raise ProfileStoreError(str(exc)) from exc

    profile = get_profile(user_id)
    if not profile:
        raise ProfileStoreError("Profile upsert succeeded but row not found")
    return profile


def _row_to_response(row: dict) -> UserProfileResponse:
    return UserProfileResponse(
        id=row["id"],
        email=row.get("email"),
        first_name=row["first_name"],
        last_name=row["last_name"],
        industry=row["industry"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def handle_profile_store_error(exc: ProfileStoreError) -> HTTPException:
    detail = str(exc)
    if _table_missing(exc):
        detail = (
            "Profiles table missing. Run backend/supabase/migrations/"
            "003_user_profiles.sql in Supabase SQL Editor."
        )
    return HTTPException(status_code=503, detail=detail)
