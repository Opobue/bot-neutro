from __future__ import annotations

import hashlib
from typing import Optional


def derive_api_key_id(api_key: Optional[str]) -> str:
    if not api_key:
        return "anonymous"
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]
