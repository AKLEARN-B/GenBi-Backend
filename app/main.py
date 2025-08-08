# ─────────────────────────────────────────────
# app/main.py
# ─────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import kb

from app.routers import (
    auth,
    advisors,
    clients,
    portfolios,
    transactions,
    content,
    quicksight_embed,
)

app = FastAPI(
    title="GenBI-Pioneers",
    version="0.1.0",
    description="FastAPI service backed by AWS Athena (CSV tables in S3)",
)

# Allow Angular dev server & other browser front-ends
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register feature routers
app.include_router(auth.router)
app.include_router(advisors.router)
app.include_router(clients.router)
app.include_router(portfolios.router)
app.include_router(transactions.router)
app.include_router(content.router)
app.include_router(quicksight_embed.router)
app.include_router(kb.router)
