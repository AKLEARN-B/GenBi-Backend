# ─────────────────────────────────────────────
# app/athena_client.py
# ─────────────────────────────────────────────
"""
Thin synchronous wrapper around boto3-Athena for quick CRUD-ish queries.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

import boto3

from app.config import settings


class AthenaClient:
    """Run SQL in Athena and return the first *N* rows as list-of-dict."""

    def __init__(self) -> None:
        self._athena = boto3.client("athena", region_name=settings.aws_region)

    # ------------------------------------------------------------------
    def query(self, sql: str, *, wait_ms: int = 1_000) -> List[Dict[str, Any]]:
        """Synchronously execute *sql* and return ≤MAX_ROWS rows."""
        res = self._athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": settings.athena_database},
            ResultConfiguration={"OutputLocation": settings.athena_output},
            WorkGroup=settings.athena_workgroup,
        )
        qid = res["QueryExecutionId"]

        # Poll status
        while True:
            meta = self._athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
            state = meta["Status"]["State"]
            if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                break
            time.sleep(wait_ms / 1000)

        if state != "SUCCEEDED":
            reason = meta["Status"].get("StateChangeReason", "unknown")
            raise RuntimeError(f"Athena query failed ({state}): {reason}")

        # Fetch first page (1 000 rows max by default)
        page = self._athena.get_query_results(
            QueryExecutionId=qid, MaxResults=settings.max_query_rows
        )

        columns = [c["Label"] for c in page["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
        rows: List[Dict[str, Any]] = []
        for r in page["ResultSet"]["Rows"][1:]:  # skip header row
            rows.append(
                {
                    col: (r["Data"][idx].get("VarCharValue") if idx < len(r["Data"]) else None)
                    for idx, col in enumerate(columns)
                }
            )
        return rows
