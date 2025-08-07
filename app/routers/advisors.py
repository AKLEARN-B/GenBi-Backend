# ─────────────────────────────────────────────
# app/routers/advisors.py
# ─────────────────────────────────────────────
from typing import List

from fastapi import APIRouter, Depends

from app.deps import get_athena_client
from app.models import Advisor, Client ,AdvisorDetail

router = APIRouter(prefix="/advisors", tags=["Advisors"])


@router.get("/", response_model=List[Advisor])
def list_advisors(athena=Depends(get_athena_client)):
    sql = "SELECT advisor_id, first_name, last_name, email FROM advisors"
    return athena.query(sql)


@router.get("/{advisor_id}/clients", response_model=List[Client])
def clients_of_advisor(advisor_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT c.client_id, c.first_name, c.last_name, c.age
        FROM clients c
        JOIN client_advisor_assignments a ON a.client_id = c.client_id
        WHERE a.advisor_id = '{advisor_id}'
    """
    return athena.query(sql)

# 3️⃣  **NEW**: full details for one advisor  ────────────────────────────
@router.get("/{advisor_id}", response_model=AdvisorDetail)
def advisor_detail(advisor_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT *
        FROM advisors
        WHERE advisor_id = '{advisor_id}'
        LIMIT 1
    """
    rows = athena.query(sql)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advisor not found",
        )
    return rows[0] 