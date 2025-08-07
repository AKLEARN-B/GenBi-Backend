# ─────────────────────────────────────────────
# app/routers/__init__.py
# ─────────────────────────────────────────────
"""
Expose feature routers for quick import in main.py
"""

from . import (
    auth,
    advisors,
    clients,
    portfolios,
    transactions,
    content,
)  # noqa: F401
