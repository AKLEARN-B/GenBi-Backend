# ─────────────────────────────────────────────
# app/routers/clients.py
# ─────────────────────────────────────────────
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_athena_client
from app.models import Client, Portfolio

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=List[Client])
def list_clients(limit: int = 100, athena=Depends(get_athena_client)):
    sql = f"SELECT client_id, first_name, last_name, age FROM clients LIMIT {limit}"
    return athena.query(sql)


@router.get("/{client_id}", response_model=Client)
def client_detail(client_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT client_id, first_name, last_name, age
        FROM clients
        WHERE client_id = '{client_id}'
        LIMIT 1
    """
    rows = athena.query(sql)
    if not rows:
        raise HTTPException(status_code=404, detail="Client not found")
    return rows[0]


@router.get("/{client_id}/portfolios", response_model=List[Portfolio])
def portfolios_for_client(client_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT portfolio_id, client_id, portfolio_name, total_value
        FROM portfolios
        WHERE client_id = '{client_id}'
    """
    return athena.query(sql)
