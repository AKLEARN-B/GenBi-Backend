# app/config.py
"""
Pydantic-v2 compliant settings loader.
Keeps env-var names in ALL_CAPS yet exposes nice snake_case fields.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",          # load .env automatically
        extra="ignore",           # ignore unexpected keys
    )

    # ---- required ----------------------------------------------------------
    aws_region: str = Field(alias="AWS_REGION")
    athena_database: str = Field(alias="ATHENA_DB")
    athena_output: str = Field(alias="ATHENA_OUTPUT")

    # ---- optional (give defaults) -----------------------------------------
    athena_workgroup: str = Field("primary", alias="ATHENA_WORKGROUP")
    max_query_rows: int = Field(1_000, alias="MAX_ROWS")


    # ---- NEW: Bedrock / KB ----
    # Use the same region for Bedrock; override via env if you need to.
    bedrock_model_arn: str = Field(
        # default model (change if you like)
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        alias="BEDROCK_MODEL_ARN",
    )
    kb_structured_id: str = Field("LKT3EYJBN2", alias="KB_STRUCTURED_ID")
    kb_unstructured_id: str = Field("ICDV1MKUJG", alias="KB_UNSTRUCTURED_ID")

settings = Settings()
