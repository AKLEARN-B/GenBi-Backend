# ─────────────────────────────────────────────
# app/routers/transactions.py
# ─────────────────────────────────────────────
from typing import List, Optional

from fastapi import APIRouter, Depends

from app.deps import get_athena_client
from app.models import Transaction

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[Transaction])
def list_transactions(
    limit: int = 200,
    client_id: Optional[str] = None,
    portfolio_id: Optional[str] = None,
    athena=Depends(get_athena_client),
):
    where = []
    if client_id:
        where.append(f"client_id = '{client_id}'")
    if portfolio_id:
        where.append(f"portfolio_id = '{portfolio_id}'")

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
        SELECT
            transaction_id,
            account_id,
            product_id,
            transaction_type,
            quantity,
            amount,
            transaction_date
        FROM transactions
        {where_sql}
        ORDER BY transaction_date DESC
        LIMIT {limit}
    """
    return athena.query(sql)
