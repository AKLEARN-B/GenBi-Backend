# recommendations.py
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from .deps import get_athena_client
from .deps import get_bedrock_client
from .config import settings
from .models import KBRecommendationsResponse, KBRecommendation

router = APIRouter(prefix="/clients", tags=["recommendations"])

def _fetch_client_and_holdings(athena, client_id: str):
    # Get client name
    row = athena.query(f"""
        SELECT client_id, first_name, last_name
        FROM clients
        WHERE client_id = '{client_id}'
        LIMIT 1
    """)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    name = f"{row[0].get('first_name','').strip()} {row[0].get('last_name','').strip()}".strip()

    # Current holdings -> product_id list
    holding_rows = athena.query(f"""
        SELECT DISTINCT product_id
        FROM portfolio_holdings
        WHERE client_id = '{client_id}'
    """)
    holdings = [r.get("product_id") for r in holding_rows if r.get("product_id")]
    return name, holdings

def _build_prompt(client_id: str, client_name: str, holdings: list, top_n: int):
    # Ask the structured KB (Redshift) to generate SQL and return STRICT JSON only.
    # Adjust table/column names here if your Redshift schema differs.
    return f"""
You are an investment assistant using the Redshift database connected to this Knowledge Base.

Goal: Recommend the top {top_n} performing products that client "{client_name}" (id: {client_id}) has NOT invested in yet.

Data assumptions (adjust to your schema if needed):
- Table products(product_id, product_name, product_type, asset_class, risk_description, is_active)
- Table product_performance(product_id, y1_return, ytd_return, sharpe_ratio)
- Table portfolio_holdings(client_id, product_id)

Rules:
- Consider only active products (is_active = true).
- Exclude products with product_id in this list: {holdings}.
- Rank primarily by y1_return (DESC). If y1_return is NULL, use ytd_return. Break ties with sharpe_ratio (DESC).
- For each recommended product, include:
  product_id, product_name, product_type, asset_class, risk_description,
  and a short reason personalized for {client_name}.

Output format:
Return ONLY valid JSON with this exact schema:
{{
  "recommendations": [
    {{
      "product_id": "string",
      "product_name": "string",
      "product_type": "string",
      "asset_class": "string",
      "risk_description": "string",
      "reason": "string"
    }}
  ]
}}
No markdown, no extra text—JSON only.
""".strip()

@router.get("/{client_id}/recommendations-kb", response_model=KBRecommendationsResponse)
def recommend_for_client_via_kb(
    client_id: str,
    top_n: int = Query(3, ge=1, le=10),
    athena = Depends(get_athena_client),
    bedrock = Depends(get_bedrock_client),
):
    client_name, holdings = _fetch_client_and_holdings(athena, client_id)
    prompt = _build_prompt(client_id, client_name, holdings, top_n)

    resp = bedrock.retrieve_and_generate(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": settings.kb_structured_id,
                "modelArn": settings.bedrock_model_arn,
            },
        },
    )

    text = (resp.get("output") or {}).get("text") or ""
    # Try to parse strict JSON; if model returns extra text, find the JSON block.
    try:
        # fast-path
        payload = json.loads(text)
    except Exception:
        import re
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise HTTPException(status_code=502, detail="KB returned non-JSON output")
        payload = json.loads(m.group(0))

    recs = []
    for r in payload.get("recommendations", [])[:top_n]:
        recs.append(KBRecommendation(**r))

    return KBRecommendationsResponse(
        client_id=client_id,
        client_name=client_name,
        recommendations=recs,
    )
