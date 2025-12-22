from __future__ import annotations

import os
from typing import Optional, Set

from .security_ids import derive_api_key_id

TIER_FREEMIUM = "freemium"
TIER_PREMIUM = "premium"
TIERS = {TIER_FREEMIUM, TIER_PREMIUM}
TIER_ORDER = {TIER_FREEMIUM: 0, TIER_PREMIUM: 1}


class TierInvalidError(ValueError):
    """Raised when a requested LLM tier is invalid."""


def _load_premium_api_key_ids() -> Set[str]:
    raw = os.getenv("MUNAY_LLM_PREMIUM_API_KEY_IDS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def normalize_requested_tier(value: str | None) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in TIERS:
        return normalized
    raise TierInvalidError(f"Invalid LLM tier: {value}")


def resolve_authorized_tier(api_key: str) -> str:
    if not api_key:
        return TIER_FREEMIUM
    premium_ids = _load_premium_api_key_ids()
    if derive_api_key_id(api_key) in premium_ids:
        return TIER_PREMIUM
    return TIER_FREEMIUM


def is_forbidden(requested: Optional[str], authorized: str) -> bool:
    if requested is None:
        return False
    authorized_rank = TIER_ORDER.get(authorized, TIER_ORDER[TIER_FREEMIUM])
    requested_rank = TIER_ORDER.get(requested, TIER_ORDER[TIER_FREEMIUM])
    return requested_rank > authorized_rank


def effective_tier(requested: Optional[str], authorized: str) -> str:
    if requested is None:
        return authorized
    if is_forbidden(requested, authorized):
        return authorized
    return requested


__all__ = [
    "TierInvalidError",
    "effective_tier",
    "is_forbidden",
    "normalize_requested_tier",
    "resolve_authorized_tier",
]
