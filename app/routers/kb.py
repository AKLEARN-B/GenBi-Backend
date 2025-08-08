# app/routers/kb.py
import logging, os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

router = APIRouter(tags=["knowledge-base"])

# ── logger (same pattern as quicksight_embed) ─────────────────────────────
logger = logging.getLogger("kb")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
    logger.addHandler(_h)

# ── env/config (like quicksight_embed) ────────────────────────────────────
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# KB IDs (use your defaults; override via env)
KB_STRUCTURED_ID   = os.getenv("KB_STRUCTURED_ID", "LKT3EYJBN2")
KB_UNSTRUCTURED_ID = os.getenv("KB_UNSTRUCTURED_ID", "ICDV1MKUJG")

# Model used by KB retrieve_and_generate (your original used Amazon Nova Pro)
KB_MODEL_ARN = os.getenv(
    "KB_MODEL_ARN",
    "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
)

# Summarization model (your original used Claude 3.5 Haiku)
SUMMARY_MODEL_ID = os.getenv(
    "BEDROCK_SUMMARY_MODEL_ID",
    "anthropic.claude-3-5-haiku-20241022-v1:0"
)

# ── boto clients (credentials via env/instance role; no hard-coded keys) ─
agent   = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
runtime = boto3.client("bedrock-runtime",        region_name=AWS_REGION)

# ── request model ─────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str

# ── helpers (function names/flow analogous to your file) ──────────────────
def getResponseFromKB(txt: str) -> str:
    """
    Your original getResponseFromKB() but without hard-coded creds and using KB_MODEL_ARN.
    """
    try:
        resp = agent.retrieve_and_generate(
            input={"text": txt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_STRUCTURED_ID,
                    "modelArn": KB_MODEL_ARN,
                },
            },
        )
        return (resp.get("output") or {}).get("text", "")
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(502, f"Bedrock (structured KB) error: {msg}")
    except Exception as e:
        raise HTTPException(502, f"Bedrock (structured KB) error: {e}")

def getResponseFromUSKB(txt: str) -> str:
    """
    Your original getResponseFromUSKB() but without hard-coded creds and using KB_MODEL_ARN.
    """
    try:
        resp = agent.retrieve_and_generate(
            input={"text": txt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_UNSTRUCTURED_ID,
                    "modelArn": KB_MODEL_ARN,
                },
            },
        )
        return (resp.get("output") or {}).get("text", "")
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(502, f"Bedrock (unstructured KB) error: {msg}")
    except Exception as e:
        raise HTTPException(502, f"Bedrock (unstructured KB) error: {e}")

def _converse_text(model_id: str, prompt: str) -> str:
    """
    Replacement for AnthropicBedrock messages.create — uses Bedrock Runtime 'converse'
    with the same effect but no explicit keys.
    """
    try:
        out = runtime.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.7},
        )
        parts = out.get("output", {}).get("message", {}).get("content", []) or []
        return "".join(p.get("text", "") for p in parts).strip()
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(502, f"Bedrock summarize error: {msg}")
    except Exception as e:
        raise HTTPException(502, f"Bedrock summarize error: {e}")

def generate_response(query: str, response1: str, response2: str) -> str:
    """
    Keep the same function name; combine two KB answers with a short LLM pass.
    (Fixes the original join bug; preserves behavior.)
    """
    prompt = (
        "You are a helpful AI assistant. Use the context below to answer the user's question.\n\n"
        f"Context:\n{response1}\n\n{response2}\n\n"
        f"User Question:\n{query}\n"
    )
    return _converse_text(SUMMARY_MODEL_ID, prompt)

# ── endpoints (exact same paths as your combinedKBResult.py) ──────────────
@router.post("/getCombinedResponse")
def getCombinedResponse(request: QueryRequest, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "-")
    logger.info("REQ /getCombinedResponse from %s | ua=%s", client_ip, ua)

    txt = request.query
    resp_structured   = getResponseFromKB(txt)
    resp_unstructured = getResponseFromUSKB(txt)
    combined          = generate_response(txt, resp_structured, resp_unstructured)

    logger.info("Combined response generated (len structured=%d, len unstructured=%d)",
                len(resp_structured), len(resp_unstructured))
    return {"answer": combined}

@router.post("/getstructuredresponse")
def getstructuredresponse(request: QueryRequest, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "-")
    logger.info("REQ /getstructuredresponse from %s | ua=%s", client_ip, ua)

    txt = request.query
    ans = getResponseFromKB(txt)
    return {"answer": ans}

@router.post("/getunstructuredresponse")
def getunstructuredresponse(request: QueryRequest, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "-")
    logger.info("REQ /getunstructuredresponse from %s | ua=%s", client_ip, ua)

    txt = request.query
    ans = getResponseFromUSKB(txt)
    return {"answer": ans}
