# ─────────────────────────────────────────────
# app/routers/auth.py
# ─────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_athena_client
from app.models import LoginRequest, LoginResponse

router = APIRouter(prefix="/login", tags=["Auth"])


@router.post("/", response_model=LoginResponse)
def login(credentials: LoginRequest, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT "UserId", "Role"
        FROM role
        WHERE "Aws User Name" = '{credentials.username}'
          AND "user_password" = '{credentials.password}'
        LIMIT 1
    """
    rows = athena.query(sql)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return {"user_id": rows[0]["UserId"], "role": rows[0]["Role"]}
