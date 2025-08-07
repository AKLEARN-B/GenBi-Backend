# ─────────────────────────────────────────────
# app/routers/content.py
# ─────────────────────────────────────────────
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_athena_client
from app.models import Content

router = APIRouter(prefix="/content", tags=["ThoughtLeadership"])


@router.get("/", response_model=List[Content])
def list_content(
    limit: int = 100,
    theme: Optional[str] = None,
    athena=Depends(get_athena_client),
):
    theme_filter = f"WHERE theme = '{theme}'" if theme else ""
    sql = f"""
        SELECT content_id, title, content_type, theme, creation_date
        FROM thought_leadership_content
        {theme_filter}
        ORDER BY creation_date DESC
        LIMIT {limit}
    """
    return athena.query(sql)


@router.get("/{content_id}", response_model=Content)
def content_detail(content_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT content_id, title, content_type, theme, creation_date
        FROM thought_leadership_content
        WHERE content_id = '{content_id}'
        LIMIT 1
    """
    rows = athena.query(sql)
    if not rows:
        raise HTTPException(status_code=404, detail="Content not found")
    return rows[0]
