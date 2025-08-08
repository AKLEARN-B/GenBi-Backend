# app/routers/quicksight_embed.py
import logging, os, re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

router = APIRouter(tags=["quicksight"])

# ── logger ────────────────────────────────────────────────────────────────
logger = logging.getLogger("quicksight_embed")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
    logger.addHandler(_h)

# ── boto client (uses env or instance role) ───────────────────────────────
qs = boto3.client("quicksight", region_name=os.getenv("AWS_REGION", "us-east-1"))

# ── request model (only 2 fields) ────────────────────────────────────────
class DashboardEmbedRequest(BaseModel):
    dashboardid: str
    userarn: str

# ── helpers ──────────────────────────────────────────────────────────────
def account_id_from_qs_user_arn(arn: str) -> str | None:
    m = re.match(r"^arn:aws:quicksight:[a-z0-9-]+:(\d{12}):user/.+$", arn)
    return m.group(1) if m else None

def summarize_qs_user_arn(arn: str | None) -> dict:
    if not arn:
        return {"present": False}
    m = re.match(r"^arn:aws:quicksight:([a-z0-9-]+):(\d{12}):user/([^/]+)/(.+)$", arn or "")
    if not m:
        return {"present": True, "raw_prefix": (arn[:16] + "...")}
    region, account, namespace, username = m.groups()
    return {"present": True, "region": region, "account": account, "namespace": namespace, "username": username}

def safe_env_snapshot() -> dict:
    return {
        "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
        "AWS_ACCOUNT_ID": os.getenv("AWS_ACCOUNT_ID"),
        "QUICKSIGHT_NAMESPACE": os.getenv("QUICKSIGHT_NAMESPACE", "default"),
        "FRONTEND_ORIGIN": os.getenv("FRONTEND_ORIGIN"),
        "QUICKSIGHT_USER_ARN": summarize_qs_user_arn(os.getenv("QUICKSIGHT_USER_ARN")),
        "AWS_ACCESS_KEY_ID_present": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "AWS_SECRET_ACCESS_KEY_present": bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
        "AWS_SESSION_TOKEN_present": bool(os.getenv("AWS_SESSION_TOKEN")),
        "boto3_credentials_provider": (
            boto3.Session().get_credentials().method if boto3.Session().get_credentials() else None
        ),
    }

# ── endpoint ─────────────────────────────────────────────────────────────
@router.post("/dashBoardEmbeddedUrl")
def generate_dashboard_embed_url(req: DashboardEmbedRequest, request: Request):
    # request logging (sanitized)
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "-")
    user_label = req.userarn.split("/")[-1] if "user/" in req.userarn else req.userarn

    logger.info(
        "REQ /dashBoardEmbeddedUrl from %s | ua=%s | dashboard_id=%s | user=%s",
        client_ip, ua, req.dashboardid, user_label
    )
    logger.info("ENV snapshot: %s", safe_env_snapshot())

    # validations
    if not req.dashboardid:
        logger.warning("Missing 'dashboardid' in request")
        raise HTTPException(status_code=400, detail="dashboardid is required")
    if not req.userarn:
        logger.warning("Missing 'userarn' in request")
        raise HTTPException(status_code=400, detail="userarn is required")

    aws_account_id = account_id_from_qs_user_arn(req.userarn) or os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        logger.error("Could not determine AWS account id | user=%s", user_label)
        raise HTTPException(
            status_code=400,
            detail="Could not determine AWS account id from userarn. Set AWS_ACCOUNT_ID env var or pass a valid QuickSight user ARN."
        )

    logger.info("Generating embed URL | account_id=%s | dashboard_id=%s | user=%s",
                aws_account_id, req.dashboardid, user_label)

    try:
        resp = qs.generate_embed_url_for_registered_user(
            AwsAccountId=aws_account_id,
            UserArn=req.userarn,
            ExperienceConfiguration={"Dashboard": {"InitialDashboardId": req.dashboardid}},
            SessionLifetimeInMinutes=600,

        )
        logger.info("Embed URL generated | expiresAt=%s", resp.get("Expiration"))
        return {"embedUrl": resp["EmbedUrl"], "expiresAt": resp.get("Expiration")}
    except ClientError as e:
        logger.exception("AWS ClientError while generating embed URL")
        raise HTTPException(status_code=500, detail=e.response.get("Error", {}).get("Message", str(e)))
    except Exception as e:
        logger.exception("Unexpected error while generating embed URL")
        raise HTTPException(status_code=500, detail=str(e))
