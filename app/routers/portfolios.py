# ─────────────────────────────────────────────
# app/routers/portfolios.py
# ─────────────────────────────────────────────
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_athena_client
from app.models import Portfolio, Holding

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.get("/{portfolio_id}", response_model=Portfolio)
def get_portfolio(portfolio_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT portfolio_id, client_id, portfolio_name, total_value
        FROM portfolios
        WHERE portfolio_id = '{portfolio_id}'
        LIMIT 1
    """
    rows = athena.query(sql)
    if not rows:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return rows[0]


@router.get("/{portfolio_id}/holdings", response_model=List[Holding])
def holdings_in_portfolio(portfolio_id: str, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT h.product_id, h.shares, h.market_value, p.product_name
        FROM portfolio_holdings h
        JOIN products p ON p.product_id = h.product_id
        WHERE h.portfolio_id = '{portfolio_id}'
    """
    return athena.query(sql)
