# ─────────────────────────────────────────────
# app/deps.py
# ─────────────────────────────────────────────
"""
FastAPI dependency helpers – gives each request access to a singleton Athena client.
"""

from functools import lru_cache

from app.athena_client import AthenaClient


@lru_cache(maxsize=1)
def get_athena_client() -> AthenaClient:  # pragma: no cover
    return AthenaClient()
