# ─────────────────────────────────────────────
# app/models.py
# ─────────────────────────────────────────────
from typing import Optional, List

from pydantic import BaseModel

# ---------- Core domain ----------


class Advisor(BaseModel):
    advisor_id: str
    first_name: str
    last_name: str
    email: Optional[str]


class Client(BaseModel):
    client_id: str
    first_name: str
    last_name: str
    age: Optional[int]


class Portfolio(BaseModel):
    portfolio_id: str
    client_id: str
    portfolio_name: str
    total_value: Optional[float]


class Holding(BaseModel):
    product_id: str
    shares: float
    market_value: float
    product_name: Optional[str]


class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    product_id: str
    transaction_type: str
    quantity: float
    amount: float
    transaction_date: str


class Content(BaseModel):
    content_id: str
    title: str
    content_type: str
    theme: str
    creation_date: str


# ---------- Auth ----------


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    role: str
