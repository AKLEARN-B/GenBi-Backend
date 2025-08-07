# ─────────────────────────────────────────────
# app/routers/auth.py
# ─────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_athena_client
from app.models import LoginRequest, LoginResponse ,UserDetails

router = APIRouter()


# app/routers/auth.py
@router.post("/login", response_model=UserDetails)
def login(credentials: LoginRequest, athena=Depends(get_athena_client)):
    sql = f"""
        SELECT
            "UserId",
            "AwsUserName",
            "User",
            "UserARN",
            "DashboardId",
            "Role",
            "Email",
            "Region"
        FROM role
        WHERE "user" = '{credentials.username}'
          AND "user_password" = '{credentials.password}'
        LIMIT 1
    """
    rows = athena.query(sql)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    # Rename keys from DB to python-friendly field names
    record = rows[0]
    return {
        "user_id":      record["UserId"],
        "aws_user_name":record["AwsUserName"],
        "user":         record["User"],
        "user_arn":     record["UserARN"],
        "dashboard_id": record["DashboardId"],
        "role":         record["Role"],
        "email":        record["Email"],
        "region":       record["Region"],
    }
