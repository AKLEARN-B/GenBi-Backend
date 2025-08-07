# ─────────────────────────────────────────────
# app/routers/clients.py
# ─────────────────────────────────────────────
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, Extra
from app.deps import get_athena_client
from app.models import Client, Portfolio

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=List[Client])
def list_clients(limit: int = 100, athena=Depends(get_athena_client)):
    sql = f"SELECT client_id, first_name, last_name, age FROM clients LIMIT {limit}"
    return athena.query(sql)


class ClientDetail(BaseModel, extra=Extra.allow):
    """
    Dynamically accepts *all* columns returned by Athena for a client
    and adds a `funds` field with the list of invested-in funds.
    """
    funds: List[str] = Field(default_factory=list, description="Funds invested in")

@router.get("/{client_id}", response_model=ClientDetail)
def client_detail(client_id: str, athena=Depends(get_athena_client)):
    # ── 1. Full client record ─────────────────────────────────────────────
    client_sql = f"""
        SELECT *
        FROM clients
        WHERE client_id = '{client_id}'
        LIMIT 1
    """
    client_rows = athena.query(client_sql)
    if not client_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    client_record = dict(client_rows[0])          # make it mutable

    # ── 2. List of funds the client holds ────────────────────────────────
    funds_sql = f"""
        SELECT DISTINCT product_name
        FROM portfolio_holdings
        WHERE client_id = '{client_id}'
          AND product_name IS NOT NULL
    """
    funds_rows = athena.query(funds_sql)
    client_record["funds"] = [row["product_name"] for row in funds_rows]

    # ── 3. Return combined result ────────────────────────────────────────
    return client_record


@router.get("/{client_id}/portfolios", response_model=List[Portfolio])
def portfolios_for_client(client_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT portfolio_id, client_id, portfolio_name, total_value
        FROM portfolios
        WHERE client_id = '{client_id}'
    """
    return athena.query(sql)
